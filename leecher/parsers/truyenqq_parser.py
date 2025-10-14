import gzip
import brotli
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from leecher.base_parser import BaseMangaParser


class TruyenQQParser(BaseMangaParser):

    TRUSTED_DOMAINS = ["hinhhinh.com", "tintruyen.net", "truyenqqgo.com"]
    VALID_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
    INVALID_IMAGE_PATTERNS = [
        ".gif",
        "logo",
        "avatar",
        "icon",
        "ads",
        "banner",
        "thumb",
        "placeholder",
    ]
    IMAGE_PRIORITY_ATTRS = ["src", "data-cdn", "data-original", "data-src", "data-url"]

    def __init__(self, session=None):
        super().__init__(session)
        self.session.headers.update({"Accept-Encoding": "gzip, deflate, br"})

    def _decompress_response(self, response) -> str:
        content = response.content
        # encoding = response.headers.get("content-encoding", "").lower()

        # try:
        #     if encoding == "gzip":
        #         content = gzip.decompress(content)
        #     elif encoding == "br":
        #         content = brotli.decompress(content)
        #     elif encoding == "deflate":
        #         import zlib

        #         content = zlib.decompress(content)
        # except Exception as e:
        #     self.logger.warning(f"Lỗi decompress ({encoding}): {e}")
        #     try:
        #         if content.startswith(b"\x1f\x8b"):
        #             content = gzip.decompress(content)
        #         elif content.startswith(b"\xce\xb2\xcf\x81"):
        #             content = brotli.decompress(content)
        #     except Exception as e2:
        #         self.logger.error(f"Auto-detect decompress fail: {e2}")

        return content.decode("utf-8", errors="ignore")

    def get_chapter_list(self, series_url: str) -> List[Dict[str, str]]:
        try:
            response = self.session.get(series_url, timeout=30)
            response.raise_for_status()

            html_text = self._decompress_response(response)
            soup = BeautifulSoup(html_text, "html.parser")

            chapters = self._extract_from_works_chapter_structure(soup, series_url)
            chapters.reverse()

            self.logger.info(f"Đã trích xuất {len(chapters)} chapters")
            return chapters

        except Exception as e:
            self.logger.error(f"Lỗi khi lấy chapter list: {e}")
            return []

    def _extract_from_works_chapter_structure(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        chapters = []
        chapter_items = soup.select(".works-chapter-list .works-chapter-item")

        if not chapter_items:
            return chapters

        for item in chapter_items:
            try:
                name_chap = item.select_one(".name-chap a")
                if not name_chap:
                    continue

                chapter_url = name_chap.get("href")
                chapter_text = self.clean_text(name_chap.get_text())

                if chapter_url:
                    chapters.append(
                        {
                            "url": self.normalize_url(chapter_url, base_url),
                            "number": self.extract_chapter_number(chapter_text),
                            "title": chapter_text,
                        }
                    )

            except Exception as e:
                self.logger.warning(f"Lỗi xử lý works-chapter-item: {e}")
                continue

        return chapters

    def _parse_chapter_links(self, links: list, base_url: str) -> List[Dict[str, str]]:
        chapters = []
        for link in links:
            try:
                chapter_url = link.get("href")
                chapter_text = self.clean_text(link.get_text())

                if chapter_url:
                    chapters.append(
                        {
                            "url": self.normalize_url(chapter_url, base_url),
                            "number": self.extract_chapter_number(chapter_text),
                            "title": chapter_text,
                        }
                    )

            except Exception as e:
                self.logger.warning(f"Lỗi xử lý chapter link: {e}")
                continue

        return chapters

    def get_image_urls(self, chapter_url: str) -> List[str]:
        try:
            response = self.session.get(chapter_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            image_urls = self._extract_from_page_chapter_structure(soup, chapter_url)
            unique_urls = self._deduplicate_and_sort(image_urls)

            self.logger.info(f"Tìm thấy {len(unique_urls)} ảnh hợp lệ")
            return unique_urls

        except Exception as e:
            self.logger.error(f"Lỗi khi lấy image URLs: {e}")
            return []

    def _extract_from_page_chapter_structure(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[str]:
        image_urls = []
        page_chapters = soup.select(".page-chapter")

        if not page_chapters:
            return image_urls

        for page_div in page_chapters:
            try:
                img = page_div.find("img")
                if not img:
                    continue

                src = self._extract_best_image_url(img)
                if src:
                    full_url = self.normalize_url(src, base_url)
                    image_urls.append(full_url)

            except Exception as e:
                self.logger.warning(f"Lỗi xử lý page: {e}")
                continue

        return image_urls

    def _extract_best_image_url(self, img_element) -> Optional[str]:
        for attr in self.IMAGE_PRIORITY_ATTRS:
            src = img_element.get(attr)
            if src and src.strip() and self.is_valid_image_url(src):
                return src
        return None

    def is_valid_image_url(self, url: str) -> bool:
        if not url:
            return False

        url_lower = url.lower()
        url_without_query = url_lower.split("?")[0]

        has_valid_ext = any(
            url_without_query.endswith(ext) for ext in self.VALID_IMAGE_EXTENSIONS
        )
        has_invalid_pattern = any(
            pattern in url_lower for pattern in self.INVALID_IMAGE_PATTERNS
        )
        is_from_trusted_source = any(
            domain in url_lower for domain in self.TRUSTED_DOMAINS
        )

        return has_valid_ext and not has_invalid_pattern and is_from_trusted_source

    def _deduplicate_and_sort(self, image_urls: List[str]) -> List[str]:
        seen = set()
        unique_urls = []
        for url in image_urls:
            if url not in seen and self.is_valid_image_url(url):
                seen.add(url)
                unique_urls.append(url)

        return self._sort_image_urls(unique_urls)

    def _sort_image_urls(self, image_urls: List[str]) -> List[str]:
        try:
            ordered_urls = [(self._extract_page_order(url), url) for url in image_urls]
            ordered_urls.sort(key=lambda x: x[0])
            return [url for _, url in ordered_urls]
        except Exception as e:
            self.logger.warning(f"Không thể sắp xếp ảnh: {e}")
            return image_urls

    def _extract_page_order(self, url: str) -> int:
        patterns = [r"/(\d+)\.(jpg|jpeg|png|webp)", r"page_(\d+)", r"/(\d+)\."]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return int(match.group(1))

        return 9999
