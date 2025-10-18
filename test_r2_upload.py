import asyncio
from io import BytesIO
from shared.logger import logging
from PIL import Image

from shared.r2_storage import R2Storage

logger = logging.getLogger(__name__)


def create_test_image(text: str = "TEST IMAGE", size: tuple = (800, 600)) -> bytes:
    """Tạo ảnh test đơn giản"""
    img = Image.new("RGB", size, color="#3498db")

    # Thêm text (optional, cần PIL)
    try:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)
        # Dùng font mặc định
        draw.text((size[0] // 2 - 50, size[1] // 2), text, fill="white")
    except:
        pass

    # Convert sang bytes
    buffer = BytesIO()
    img.save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


async def test_upload_single_file():
    """Test upload 1 file đơn giản"""
    logger.info("=== TEST 1: Upload single file ===")

    try:
        r2 = R2Storage()

        # Tạo test image
        image_data = create_test_image("Single Test")

        # Upload
        object_key = "test/single_test.webp"
        success, public_url = r2.upload_file(
            file_data=image_data, object_key=object_key, content_type="image/webp"
        )

        if success:
            logger.info(f"✅ Upload thành công!")
            logger.info(f"📎 URL: {public_url}")
            return True
        else:
            logger.error("❌ Upload thất bại")
            return False

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


async def test_file_operations():
    """Test các operations khác"""
    logger.info("\n=== TEST 3: File operations ===")

    try:
        r2 = R2Storage()
        test_key = "test/operations_test.webp"

        # 1. Upload
        logger.info("1️⃣ Uploading test file...")
        image_data = create_test_image("Operations Test")
        success, url = r2.upload_file(image_data, test_key)

        if not success:
            logger.error("❌ Upload failed")
            return False
        logger.info(f"✅ Uploaded: {url}")

        # 2. Get public URL
        logger.info("\n3️⃣ Getting public URL...")
        public_url = r2.get_public_url(test_key)
        logger.info(f"📎 Public URL: {public_url}")

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


async def main():
    """Chạy tất cả tests"""
    logger.info("🚀 Bắt đầu test R2 Upload\n")

    try:
        # Test 1: Single file
        test1 = await test_upload_single_file()

        # Test 2: File operations
        test2 = await test_file_operations()

        # Tổng kết
        logger.info("\n" + "=" * 50)
        logger.info("📊 KẾT QUẢ TỔNG HỢP")
        logger.info("=" * 50)
        logger.info(f"Test 1 - Single Upload:    {'✅ PASS' if test1 else '❌ FAIL'}")
        logger.info(f"Test 2 - Multiple Upload:  {'✅ PASS' if test2 else '❌ FAIL'}")

        all_pass = all([test1, test2])
        logger.info("=" * 50)
        logger.info(f"{'🎉 TẤT CẢ TESTS PASS!' if all_pass else '⚠️  CÓ TESTS FAILED'}")

    except Exception as e:
        logger.error(f"❌ Lỗi chạy tests: {e}")


if __name__ == "__main__":
    asyncio.run(main())
