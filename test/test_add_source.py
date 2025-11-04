import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager
from shared.logger import logging


async def test_source():
    db = LeecheDatabaseManager()

    try:
        if not await db.connect():
            return

        print("🧪 Testing Add Source...")

        print("1. Thêm manga source...")
        source = await db.add_manga_source(
            name="truyenqq",
            base_url="https://truyenqqgo.com",
            parser_class="TruyenQQParser",
        )
        if source:
            print(f"✅ Đã thêm source: {source.name}")

        print("🎉 Tất cả tests passed!")

    except Exception as e:
        logging.error(f"❌ Lỗi test: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_source())
