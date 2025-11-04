import asyncio
import logging
from database.leech_manager import LeecheDatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_leech_manager():
    db = LeecheDatabaseManager()

    try:
        if not await db.connect():
            return

        print("🧪 Testing leech manager...")

        # 1. Thêm source
        print("1. Thêm manga source...")
        source = await db.add_manga_source(
            name="truyenqq",
            base_url="https://truyenqqgo.com",
            parser_class="TruyenQQParser",
        )
        if source:
            print(f"✅ Đã thêm source: {source.name}")

        # 2. Thêm truyện
        print("2. Thêm manga series...")
        series = await db.add_manga_series(
            source_name="truyenqq",
            title="Thức Tỉnh Toàn Chức",
            target_url="https://truyenqqgo.com/truyen-tranh/thuc-tinh-toan-chuc-18865",
            description="Truyện tranh Thức Tỉnh Toàn Chức được cập nhật nhanh và đầy đủ nhất tại TruyenQQ. Bạn đọc đừng quên để lại bình luận và chia sẻ, ủng hộ TruyenQQ ra các chương mới nhất của truyện Thức Tỉnh Toàn Chức.",
        )
        if series:
            print(f"✅ Đã thêm series: {series.title}")

        # 3. Thêm chapter
        # print("3. Thêm chapter...")
        # chapter = await db.add_chapter(
        #     series_id=series.id,
        #     chapter_number="1",
        #     chapter_title="Chapter 1",
        #     chapter_url="https://www.nettruyen.com/one-piece/chapter-1",
        # )
        # if chapter:
        #     print(f"   ✅ Đã thêm chapter: {chapter.chapter_number}")

        # 4. Thêm ảnh
        # print("4. Thêm chapter images...")
        # image = await db.add_chapter_image(
        #     chapter_id=chapter.id,
        #     image_url="https://example.com/image1.jpg",
        #     image_order=1,
        #     local_path="/images/one-piece/chapter-1/001.jpg",
        #     file_size=102400,
        # )
        # if image:
        #     print(f"   ✅ Đã thêm ảnh: order {image.image_order}")

        # 5. Cập nhật trạng thái chapter
        # print("5. Cập nhật chapter status...")
        # await db.update_chapter_status(chapter.id, "COMPLETED", image_count=1)
        # print("   ✅ Đã cập nhật status chapter")

        # 6. Lấy pending series
        print("6. Lấy pending series...")
        pending_series = await db.get_pending_series()
        print(f"✅ Số pending series: {len(pending_series)}")

        print("🎉 Tất cả tests passed!")

    except Exception as e:
        logging.error(f"❌ Lỗi test: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_leech_manager())
