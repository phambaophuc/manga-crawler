import asyncio
import logging

from database.leech_manager import LeecheDatabaseManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_schema():
    db = LeecheDatabaseManager()

    try:
        if not await db.connect():
            return

        if not await db.health_check():
            return

        print("🎉 Schema đã được tạo thành công!")
    except Exception as e:
        logging.error(f"❌ Lỗi test schema: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_schema())
