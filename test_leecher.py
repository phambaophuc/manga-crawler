import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager
from leecher.manga_leecher import MangaLeecher

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_leecher():
    """Test core leecher"""
    db = LeecheDatabaseManager()
    leecher = MangaLeecher(db)

    try:
        # Kết nối database
        if not await db.connect():
            return

        print("🧪 Testing core leecher...")

        # Thêm series test
        series = await db.add_manga_series(
            source_name="truyenqq",
            title="Ngự Thú Tiến Hóa",
            target_url="https://truyenqqgo.com/truyen-tranh/ngu-thu-tien-hoa-22033",
            description="Truyện tranh Ngự Thú Tiến Hóa",
        )

        if series:
            print(f"✅ Đã thêm series test: {series.title}")

            # Test leecher (sẽ fail vì chưa có parser thật)
            success = await leecher.download_series(series.id)
            print(f"✅ Kết quả leech: {success}")

        print("🎉 Core leecher test completed!")

    except Exception as e:
        logging.error(f"❌ Lỗi test: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_leecher())
