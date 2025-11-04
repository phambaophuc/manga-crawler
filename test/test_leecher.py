import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager
from leecher.manga_leecher import MangaLeecher

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_leecher():
    db = LeecheDatabaseManager()
    leecher = MangaLeecher(db)

    try:
        if not await db.connect():
            return

        print("🧪 Testing core leecher...")

        series = await db.add_manga_series(
            source_name="truyenqq",
            title="Sensei, Bokutachi Wa Koroshiteimasen",
            target_url="https://truyenqqgo.com/truyen-tranh/sensei-bokutachi-wa-koroshiteimasen-22126",
            description="Truyện tranh Sensei, Bokutachi Wa Koroshiteimasen.",
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
