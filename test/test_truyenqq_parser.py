import logging
from leecher.parsers.truyenqq_parser import TruyenQQParser
from shared.logger import logging


def test_truyenqq_parser():
    parser = TruyenQQParser()

    try:
        print("🧪 Testing TruyenQQ Parser...")

        test_series_url = (
            "https://truyenqqgo.com/truyen-tranh/lao-xa-tu-tien-truyen-16211"
        )
        test_chapter_url = "https://truyenqqgo.com/truyen-tranh/lao-xa-tu-tien-truyen-16211-chap-12.html"

        print(f"1. Testing chapter list from: {test_series_url}")
        chapters = parser.get_chapter_list(test_series_url)
        print(f"   ✅ Found {len(chapters)} chapters")

        if chapters:
            for i, chapter in enumerate(chapters[:15]):
                print(f"   {i+1}. {chapter['number']} - {chapter['title']}")
                print(f"      URL: {chapter['url']}")

        print(f"\n2. Testing image URLs from: {test_chapter_url}")
        image_urls = parser.get_image_urls(test_chapter_url)
        print(f"   ✅ Found {len(image_urls)} images")

        if image_urls:
            for i, url in enumerate(image_urls[:3]):
                print(f"   {i+1}. {url}")

        print("\n🎉 TruyenQQ parser test completed!")

    except Exception as e:
        logging.error(f"❌ Lỗi test: {e}")


if __name__ == "__main__":
    test_truyenqq_parser()
