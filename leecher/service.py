import asyncio
import logging
import signal

from aiolimiter import AsyncLimiter
from leecher.manga_leecher import MangaLeecher
from leecher import ParserFactory


class MangaLeechService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.leecher = MangaLeecher(self.db, enable_r2=True)
        self.logger = logging.getLogger(__name__)
        self._stop_event = asyncio.Event()
        self._register_parsers()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.logger.info(f"Nhận signal {signum}, đang dừng...")
        self.stop()

    def _register_parsers(self):
        try:
            from leecher.parsers.truyenqq_parser import TruyenQQParser

            ParserFactory.register_parser("truyenqq", TruyenQQParser)
        except Exception as e:
            self.logger.error(f"Lỗi đăng ký parser: {e}")

    async def start(self):
        if not await self.db.connect():
            self.logger.error("Kết nối database thất bại")
            return

        reset_count = await self.db.reset_stuck_downloads()
        if reset_count > 0:
            self.logger.info(f"Reset {reset_count} chapters đang download dở")

        try:
            await self._process_pending_series()

        except KeyboardInterrupt:
            self.logger.info("Service dừng bởi người dùng")
        except Exception as e:
            self.logger.error(f"Lỗi service: {e}")
        finally:
            await self.db.disconnect()
            self.logger.info("Đã chạy xong và dừng dịch vụ.")

    async def _process_pending_series(self):
        try:
            pending_series = await self.db.get_pending_series()
            if not pending_series:
                return

            self.logger.info(f"Xử lý {len(pending_series)} series")

            rate_limiter = AsyncLimiter(max_rate=1, time_period=3)
            semaphore = asyncio.Semaphore(3)

            async def process_one(series):
                if self._stop_event.is_set():
                    return

                if series.source.name not in ParserFactory.get_available_sources():
                    self.logger.error(f"Source không hỗ trợ: {series.source.name}")
                    return

                try:
                    async with rate_limiter:
                        async with semaphore:
                            if self._stop_event.is_set():
                                return
                            success = await self.leecher.download_series(series.id)
                            level = self.logger.info if success else self.logger.error
                            level(f"{'✅' if success else '❌'} {series.title}")
                except asyncio.CancelledError:
                    self.logger.info(f"❌ {series.title} bị dừng giữa chừng")
                    return

            self._tasks = [
                asyncio.create_task(process_one(series)) for series in pending_series
            ]
            await asyncio.gather(*self._tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Lỗi xử lý series: {e}")

    def stop(self):
        self.logger.info("Đang dừng service ngay lập tức...")
        self._stop_event.set()
        if hasattr(self, "_tasks"):
            for task in self._tasks:
                task.cancel()
