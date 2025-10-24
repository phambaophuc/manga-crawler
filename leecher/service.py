import asyncio
import logging
import signal
from leecher.manga_leecher import MangaLeecher
from leecher import ParserFactory


class MangaLeechService:
    def __init__(self, db_manager, check_interval: int = 60):
        self.db = db_manager
        self.leecher = MangaLeecher(self.db, enable_r2=True)
        self.check_interval = check_interval
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

        self.logger.info("Manga Leech Service khởi động...")

        try:
            while not self._stop_event.is_set():
                await self._process_pending_series()
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self.check_interval
                    )
                except asyncio.TimeoutError:
                    pass

        except KeyboardInterrupt:
            self.logger.info("Service dừng bởi người dùng")
        except Exception as e:
            self.logger.error(f"Lỗi service: {e}")
        finally:
            await self.db.disconnect()
            self.logger.info("Đã dừng dịch vụ.")

    async def _process_pending_series(self):
        try:
            pending_series = await self.db.get_pending_series()

            if not pending_series:
                return

            self.logger.info(f"Xử lý {len(pending_series)} series")

            for i, series in enumerate(pending_series):
                if self._stop_event.is_set():
                    break

                if series.source.name not in ParserFactory.get_available_sources():
                    self.logger.error(f"Source không hỗ trợ: {series.source.name}")
                    continue

                if i > 0:
                    self.logger.info("⏳ Chờ 3s...")
                    try:
                        await asyncio.wait_for(self._stop_event.wait(), timeout=3.0)
                    except asyncio.TimeoutError:
                        pass
                    if self._stop_event.is_set():
                        break

                success = await self.leecher.download_series(series.id)
                level = self.logger.info if success else self.logger.error
                level(f"{'✅' if success else '❌'} {series.title}")

        except Exception as e:
            self.logger.error(f"Lỗi xử lý series: {e}")

    def stop(self):
        self._stop_event.set()
