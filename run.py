import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager
from leecher.service import MangaLeechService


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main():
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Manga Leech Service...")

    service = MangaLeechService(db_manager=LeecheDatabaseManager(), check_interval=30)

    try:
        await service.start()
    except Exception as e:
        logger.error(f"❌ Service error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
