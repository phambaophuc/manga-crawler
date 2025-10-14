import requests


def test_image_download():
    """Test tải 1 ảnh với headers"""
    # Lấy 1 URL ảnh từ log của bạn
    test_image_url = (
        "https://s135.hinhhinh.com/20199/1/0.jpg?gt=hdfgdfg"  # Thay bằng URL thật
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://truyenqqgo.com/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }

    response = requests.get(test_image_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")


if __name__ == "__main__":
    test_image_download()
