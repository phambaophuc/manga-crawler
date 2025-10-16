import asyncio
from pathlib import Path
import re
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict
import logging
from leecher.parser_factory import ParserFactory


class MangaLeecher:
    """Core leecher cho truyện tranh"""

    DEFAULT_TIMEOUT = 30
    DELAY_BETWEEN_CHAPTERS = 2
    DELAY_BETWEEN_IMAGES = 0.1
    CONTENT_TYPE_MAP = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp"}

    def __init__(self, db_manager, storage_path: str = "manga_storage"):
        self.db = db_manager
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_pool: Dict[str, requests.Session] = {}
        self.logger = logging.getLogger(__name__)

    def get_session_for_source(self, source_name: str) -> requests.Session:
        if source_name not in self.session_pool:
            session = requests.Session()
            retry_strategy = Retry(total=3, backoff_factor=1)
            adapter = HTTPAdapter(
                pool_connections=10, pool_maxsize=10, max_retries=retry_strategy
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            self.session_pool[source_name] = session
        return self.session_pool[source_name]

    async def download_series(self, series_id: int) -> bool:
        try:
            series = await self.db.get_series_by_id(series_id)
            if not series:
                self.logger.error(f"Series {series_id} không tìm thấy")
                return False

            self.logger.info(f"📖 Tải: {series.title} [{series.source.name}]")

            session = self.get_session_for_source(series.source.name)
            parser = ParserFactory.create_parser(series.source.name, session)

            web_chapters = parser.get_chapter_list(series.target_url)
            if not web_chapters:
                self.logger.error(f"Không tìm thấy chapter: {series.title}")
                return False

            db_chapters = await self.db.get_chapters_by_series(
                series_id, include_deleted=True
            )

            if len(web_chapters) == len(db_chapters):
                self.logger.info(
                    f"✅ Series '{series.title}' đã có đủ chapters, bỏ qua"
                )
                return True

            self.logger.info(
                f"🚀 Tải {len(web_chapters) - len(db_chapters)} chapters mới..."
            )

            success_count = len(db_chapters)
            for chapter_info in web_chapters:
                existing = await self.db.get_chapter_by_url(
                    series_id, chapter_info["url"]
                )
                if existing:
                    continue

                chapter = await self.db.add_chapter(
                    series_id=series_id,
                    chapter_number=chapter_info["number"],
                    chapter_title=chapter_info["title"],
                    chapter_url=chapter_info["url"],
                )

                if chapter and await self._download_chapter(
                    parser,
                    chapter.id,
                    chapter_info["url"],
                    series.title,
                    chapter_info["number"],
                    series.source.name,
                ):
                    success_count += 1

                await asyncio.sleep(self.DELAY_BETWEEN_CHAPTERS)

            self.logger.info(
                f"✅ Hoàn thành: {success_count}/{len(web_chapters)} chapters"
            )
            return success_count == len(web_chapters)

        except Exception as e:
            self.logger.error(f"Lỗi tải series {series_id}: {e}")
            return False

    async def _download_chapter(
        self,
        parser,
        chapter_id: int,
        chapter_url: str,
        series_title: str,
        chapter_number: str,
        source_name: str,
    ) -> bool:
        try:
            await self.db.update_chapter_status(chapter_id, "DOWNLOADING")

            image_urls = parser.get_image_urls(chapter_url)
            if not image_urls:
                self.logger.warning(f"Chapter {chapter_id}: không có ảnh")
                await self.db.update_chapter_status(chapter_id, "FAILED")
                return False

            existing_images = await self.db.get_chapter_images(chapter_id)
            completed_orders = {
                img.image_order
                for img in existing_images
                if img.download_status == "COMPLETED" and img.local_path
            }

            self.logger.info(
                f"📊 {series_title} - Chapter {chapter_number}: {len(completed_orders)}/{len(image_urls)} ảnh đã hoàn thành"
            )

            images_to_download = [
                (i, url)
                for i, url in enumerate(image_urls, 1)
                if i not in completed_orders
            ]

            if not images_to_download:
                self.logger.info(f"✅ Chapter {chapter_number} đã hoàn thành")
                await self.db.update_chapter_status(
                    chapter_id, "COMPLETED", len(image_urls)
                )
                return True

            self.logger.info(f"🚀 Tải song song {len(images_to_download)} ảnh...")

            parallel_success = await self._download_images_parallel(
                chapter_id,
                images_to_download,
                series_title,
                chapter_number,
                source_name,
            )
            success_count = len(completed_orders) + parallel_success
            status = "COMPLETED" if success_count == len(image_urls) else "PARTIAL"

            await self.db.update_chapter_status(chapter_id, status, success_count)
            log_icon = "✅" if status == "COMPLETED" else "⚠️"
            self.logger.info(
                f"{log_icon} {series_title} - Chapter {chapter_number}: {success_count}/{len(image_urls)} ảnh"
            )

            return success_count > 0

        except Exception as e:
            self.logger.error(f"Lỗi chapter {chapter_number}: {e}")
            await self.db.update_chapter_status(chapter_id, "FAILED")
            return False

    @staticmethod
    def _get_series_folder_name(series_title: str) -> str:
        """Tạo tên folder từ tiêu đề truyện"""
        slug = re.sub(r"[^\w\s-]", "", series_title.lower())
        return re.sub(r"[-\s]+", "-", slug).strip("-_")

    async def _download_image_sync(
        self,
        chapter_id: int,
        image_url: str,
        order: int,
        series_title: str,
        chapter_number: str,
        source_name: str,
    ) -> bool:
        try:
            series_slug = self._get_series_folder_name(series_title)
            chapter_folder = (
                self.storage_path / series_slug / f"chapter_{chapter_number}"
            )
            chapter_folder.mkdir(parents=True, exist_ok=True)

            session = self.get_session_for_source(source_name)
            headers = {"Referer": "https://truyenqqgo.com/"}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: session.get(
                    image_url, headers=headers, timeout=self.DEFAULT_TIMEOUT
                ),
            )

            if response.status_code != 200:
                self.logger.error(f"HTTP {response.status_code}: ảnh {order}")
                return False

            ext = self._get_image_extension(response, image_url)
            filepath = chapter_folder / f"{order:03d}.{ext}"

            await loop.run_in_executor(
                None, lambda: filepath.write_bytes(response.content)
            )

            relative_path = f"{series_slug}/chapter_{chapter_number}/{filepath.name}"
            await self.db.add_chapter_image(
                chapter_id=chapter_id,
                image_url=image_url,
                image_order=order,
                local_path=str(relative_path),
                file_size=len(response.content),
            )

            self.logger.debug(f"✅ Ảnh {order}: {filepath.name}")
            await asyncio.sleep(self.DELAY_BETWEEN_IMAGES)
            return True

        except Exception as e:
            self.logger.error(f"Lỗi ảnh {order}: {e}")
            return False

    async def _download_images_parallel(
        self,
        chapter_id: int,
        images_to_download: list,
        series_title: str,
        chapter_number: str,
        source_name: str,
    ) -> int:
        tasks = [
            self._download_image_sync(
                chapter_id,
                url,
                order,
                series_title,
                chapter_number,
                source_name,
            )
            for order, url in images_to_download
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        self.logger.info(f"✅ Đã tải {success_count}/{len(images_to_download)} ảnh")
        return success_count

    @staticmethod
    def _get_image_extension(response: requests.Response, image_url: str) -> str:
        content_type = response.headers.get("content-type", "").lower()

        for key, ext in MangaLeecher.CONTENT_TYPE_MAP.items():
            if key in content_type:
                return ext

        path = urlparse(image_url).path
        return path.split(".")[-1] if "." in path else "jpg"
