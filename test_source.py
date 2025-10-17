import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_source():
    """Test các phương thức leech truyện"""
    db = LeecheDatabaseManager()

    try:
        # Kết nối database
        if not await db.connect():
            return

        print("🧪 Testing Add Source...")

        # 1. Thêm source
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
