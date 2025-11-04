import asyncio
from datetime import datetime
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.leech_manager import LeecheDatabaseManager
from leecher.service import MangaLeechService
from shared.logger import logging

logger = logging.getLogger(__name__)


async def run_manga_service():
    logger.info(f"🚀 Bắt đầu chạy Manga Leech Service: {datetime.now()}")
    service = MangaLeechService(db_manager=LeecheDatabaseManager())
    await service._process_pending_series()
    logger.info(f"✅ Kết thúc Manga Leech Service: {datetime.now()}")


def main():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(run_manga_service, "cron", hour=0, minute=0)
    scheduler.add_job(run_manga_service, "cron", hour=12, minute=0)

    scheduler.start()
    logger.info("Scheduler đã chạy, đang chờ thời gian chạy nhiệm vụ...")

    try:
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        logger.info("Scheduler dừng")


if __name__ == "__main__":
    main()
