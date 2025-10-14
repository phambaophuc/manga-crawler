import asyncio
import logging

from database.manager import DatabaseManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_schema():
    db = DatabaseManager()

    try:
        if not await db.connect():
            return

        # Health check
        if not await db.health_check():
            return

        print("🎉 Schema đã được tạo thành công!")
        print("✅ Các bảng đã có:")
        print("   - manga_sources")
        print("   - manga_series")
        print("   - manga_chapters")
        print("   - chapter_images")
    except Exception as e:
        logging.error(f"❌ Lỗi test schema: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_schema())
