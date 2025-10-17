import asyncio
import logging
import signal
from leecher.manga_leecher import MangaLeecher
from leecher import ParserFactory


class MangaLeechService:
    def __init__(self, db_manager, check_interval: int = 60):
        self.db = db_manager
        self.leecher = MangaLeecher(self.db)
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        self.is_running = False
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
        self.is_running = True

        if not await self.db.connect():
            self.logger.error("Kết nối database thất bại")
            return

        reset_count = await self.db.reset_stuck_downloads()
        if reset_count > 0:
            self.logger.info(f"Reset {reset_count} chapters đang download dở")

        self.logger.info("Manga Leech Service khởi động...")

        try:
            while self.is_running:
                await self._process_pending_series()
                await asyncio.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Service dừng bởi người dùng")
        except Exception as e:
            self.logger.error(f"Lỗi service: {e}")
        finally:
            await self.db.disconnect()
            self.is_running = False
            self.logger.info("Đã dừng dịch vụ.")

    async def _process_pending_series(self):
        try:
            pending_series = await self.db.get_pending_series()

            if not pending_series:
                return

            self.logger.info(f"Xử lý {len(pending_series)} series")

            for series in pending_series:
                if series.source.name not in ParserFactory.get_available_sources():
                    self.logger.error(f"Source không hỗ trợ: {series.source.name}")
                    continue

                success = await self.leecher.download_series(series.id)
                level = self.logger.info if success else self.logger.error
                level(f"{'✅' if success else '❌'} {series.title}")

        except Exception as e:
            self.logger.error(f"Lỗi xử lý series: {e}")

    def stop(self):
        self.is_running = False
