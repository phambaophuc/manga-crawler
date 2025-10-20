import asyncio
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict
import logging
from leecher.parser_factory import ParserFactory
from shared.image_utils import ImageConverter
from shared.r2_storage import R2Storage
from shared.storage_utils import StorageUtils


class MangaLeecher:
    """Core leecher cho truyện tranh"""

    DEFAULT_TIMEOUT = 30
    DELAY_BETWEEN_CHAPTERS = 3
    DELAY_BETWEEN_IMAGES = 0.3
    MAX_CONCURRENT_CHAPTERS = 2
    MAX_CONCURRENT_IMAGES = 15
    WEBP_QUALITY = 85

    def __init__(
        self, db_manager, storage_path: str = "manga_storage", enable_r2: bool = False
    ):
        self.db = db_manager
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_pool: Dict[str, requests.Session] = {}
        self.logger = logging.getLogger(__name__)
        self.chapter_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_CHAPTERS)
        self.image_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_IMAGES)
        self.image_converter = ImageConverter()

        # R2 Storage
        self.enable_r2 = enable_r2
        self.r2_storage = R2Storage() if enable_r2 else None

    def get_session_for_source(self, source_name: str) -> requests.Session:
        if source_name not in self.session_pool:
            session = requests.Session()
            retry_strategy = Retry(
                total=3, backoff_factor=2, respect_retry_after_header=True
            )
            adapter = HTTPAdapter(
                pool_connections=5, pool_maxsize=15, max_retries=retry_strategy
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

            chapters_to_download = []
            for chapter_info in web_chapters:
                if not await self.db.get_chapter_by_url(series_id, chapter_info["url"]):
                    chapters_to_download.append(chapter_info)

            self.logger.info(f"🚀 Tải {len(chapters_to_download)} chapters mới")

            tasks = [
                self._download_chapter_task(
                    parser,
                    series_id,
                    ch,
                    series.title,
                    series.source.name,
                    series.source.base_url,
                )
                for ch in chapters_to_download
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = len(db_chapters) + sum(1 for r in results if r is True)
            self.logger.info(
                f"✅ Hoàn thành: {success_count}/{len(web_chapters)} chapters"
            )
            return success_count == len(web_chapters)

        except Exception as e:
            self.logger.error(f"Lỗi tải series {series_id}: {e}")
            return False

    async def _download_chapter_task(
        self,
        parser,
        series_id: int,
        chapter_info: dict,
        series_title: str,
        source_name: str,
        source_url: str,
    ) -> bool:
        async with self.chapter_semaphore:
            try:
                chapter_number = self.parse_chapter_number(chapter_info["number"])
                chapter = await self.db.add_chapter(
                    series_id=series_id,
                    chapter_number=chapter_number,
                    chapter_title=chapter_info["title"],
                    chapter_url=chapter_info["url"],
                )
                if not chapter:
                    return False

                result = await self._download_chapter(
                    parser,
                    chapter.id,
                    chapter_info["url"],
                    series_title,
                    chapter_number,
                    source_name,
                    source_url,
                )
                await asyncio.sleep(self.DELAY_BETWEEN_CHAPTERS)
                return result

            except Exception as e:
                self.logger.error(f"Lỗi chapter {chapter_info['number']}: {e}")
                return False

    async def _download_chapter(
        self,
        parser,
        chapter_id: int,
        chapter_url: str,
        series_title: str,
        chapter_number: float,
        source_name: str,
        source_url: str,
    ) -> bool:
        try:
            await self.db.update_chapter_status(chapter_id, "DOWNLOADING")

            image_urls = parser.get_image_urls(chapter_url)
            if not image_urls:
                self.logger.warning(f"Chapter {chapter_number}: không có ảnh")
                await self.db.update_chapter_status(chapter_id, "FAILED")
                return False

            existing_images = await self.db.get_chapter_images(chapter_id)
            completed_orders = {
                img.image_order
                for img in existing_images
                if img.download_status == "COMPLETED" and img.local_path
            }

            images_to_download = [
                (i, url)
                for i, url in enumerate(image_urls, 1)
                if i not in completed_orders
            ]

            self.logger.info(
                f"📊 {series_title} - Chapter {chapter_number}: {len(completed_orders)}/{len(image_urls)} ảnh đã hoàn thành"
            )

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
                source_url,
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

    async def _download_images_parallel(
        self,
        chapter_id: int,
        images_to_download: list,
        series_title: str,
        chapter_number: float,
        source_name: str,
        source_url: str,
    ) -> int:
        tasks = [
            self._download_image_task(
                chapter_id,
                url,
                order,
                series_title,
                chapter_number,
                source_name,
                source_url,
            )
            for order, url in images_to_download
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        image_records = [r for r in results if isinstance(r, dict)]
        success_count = len(image_records)
        if success_count > 0:
            await self.db.bulk_add_chapter_images(image_records)

        self.logger.info(f"✅ Đã tải {success_count}/{len(images_to_download)} ảnh")
        return success_count

    async def _download_image_task(
        self,
        chapter_id: int,
        image_url: str,
        order: int,
        series_title: str,
        chapter_number: float,
        source_name: str,
        source_url: str,
    ) -> bool:
        try:
            session = self.get_session_for_source(source_name)
            headers = {"Referer": source_url}

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

            # Convert to WebP
            webp_data, file_size = await loop.run_in_executor(
                None,
                self.image_converter.to_webp,
                response.content,
                self.WEBP_QUALITY,
            )

            # Create object key for R2
            safe_series = StorageUtils.sanitize_filename(series_title)
            safe_chapter = StorageUtils.sanitize_filename(f"chapter_{chapter_number}")
            r2_object_key = f"{safe_series}/{safe_chapter}/{order:03d}.webp"

            # Upload to R2
            if self.enable_r2 and self.r2_storage:
                success, public_url = await loop.run_in_executor(
                    None,
                    self.r2_storage.upload_file,
                    webp_data,
                    r2_object_key,
                    "image/webp",
                )

                if not success:
                    self.logger.error(f"❌ R2 upload failed: ảnh {order}")
                    return False

                storage_path = public_url
            else:
                chapter_folder = StorageUtils.create_directory_structure(
                    self.storage_path, series_title, chapter_number
                )
                filepath = chapter_folder / f"{order:03d}.webp"
                await loop.run_in_executor(
                    None, lambda: filepath.write_bytes(webp_data)
                )
                storage_path = str(
                    StorageUtils.get_relative_path(self.storage_path, filepath)
                )

            await asyncio.sleep(self.DELAY_BETWEEN_IMAGES)
            return {
                "chapter_id": chapter_id,
                "image_url": image_url,
                "image_order": order,
                "local_path": storage_path,
                "file_size": file_size,
                "download_status": "COMPLETED",
            }

        except Exception as e:
            self.logger.error(f"Lỗi ảnh {order}: {e}")
            return None

    @staticmethod
    def parse_chapter_number(value: str):
        try:
            num = float(value)
            return int(num) if num.is_integer() else num
        except (ValueError, TypeError):
            return None
