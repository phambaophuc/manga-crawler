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
    await service.start()
    logger.info(f"✅ Kết thúc Manga Leech Service: {datetime.now()}")


async def main():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(run_manga_service, "cron", hour=0, minute=0)
    scheduler.add_job(run_manga_service, "cron", hour=20, minute=15)

    scheduler.start()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
