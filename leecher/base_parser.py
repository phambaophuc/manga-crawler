from abc import ABC, abstractmethod
from urllib.parse import urljoin
import requests
import re
import logging
from typing import List, Dict


class BaseMangaParser(ABC):
    """Abstract base class cho tất cả parser"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    INVALID_PATTERNS = {".gif", "logo", "avatar", "icon", "ads"}
    CHAPTER_PATTERNS = [
        r"chương\s*(\d+\.?\d*)",
        r"chap\s*(\d+\.?\d*)",
        r"chapter\s*(\d+\.?\d*)",
        r"(\d+\.?\d+)",
    ]

    def __init__(self, session: requests.Session = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.HEADERS)
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_chapter_list(self, series_url: str) -> List[Dict[str, str]]:
        """Lấy danh sách chapter từ trang truyện"""
        pass

    @abstractmethod
    def get_image_urls(self, chapter_url: str) -> List[str]:
        """Lấy danh sách URL ảnh từ chapter"""
        pass

    def extract_chapter_number(self, text: str) -> str:
        """Trích xuất số chapter từ text"""
        text = self.clean_text(text).lower()

        for pattern in self.CHAPTER_PATTERNS:
            if match := re.search(pattern, text):
                number = match.group(1)
                if number.replace(".", "").isdigit():
                    return number

        return text

    @staticmethod
    def normalize_url(url: str, base_url: str = "") -> str:
        """Chuẩn hóa URL"""
        return urljoin(base_url, url) if url else ""

    @staticmethod
    def clean_text(text: str) -> str:
        """Làm sạch text"""
        return re.sub(r"\s+", " ", text).strip() if text else ""

    def is_valid_image_url(self, url: str) -> bool:
        """Kiểm tra URL ảnh hợp lệ"""
        if not url:
            return False

        url_lower = url.lower()
        return any(
            url_lower.endswith(ext) for ext in self.VALID_EXTENSIONS
        ) and not any(pattern in url_lower for pattern in self.INVALID_PATTERNS)
