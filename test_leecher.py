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
            title="Thức Tỉnh Toàn Chức",
            target_url="https://truyenqqgo.com/truyen-tranh/thuc-tinh-toan-chuc-18865",
            description="Truyện tranh Thức Tỉnh Toàn Chức được cập nhật nhanh và đầy đủ nhất tại TruyenQQ. Bạn đọc đừng quên để lại bình luận và chia sẻ, ủng hộ TruyenQQ ra các chương mới nhất của truyện Thức Tỉnh Toàn Chức.",
        )

        if series:
            print(f"✅ Đã thêm series test: {series.title}")

            success = await leecher.download_series(series.id)
            print(f"✅ Kết quả leech: {success}")

        print("🎉 Core leecher test completed!")

    except Exception as e:
        logging.error(f"❌ Lỗi test: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_leecher())
