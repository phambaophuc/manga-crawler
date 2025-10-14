from prisma import Prisma
from prisma.models import MangaSource, MangaSeries, MangaChapter, ChapterImage
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging


class LeecheDatabaseManager:
    def __init__(self) -> None:
        self.db: Prisma = Prisma()
        self.logger: logging.Logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        """Kết nối database"""
        try:
            await self.db.connect()
            self.logger.info("✅ Đã kết nối database")
            return True
        except Exception as e:
            self.logger.error(f"❌ Lỗi kết nối database: {e}")
            return False

    async def disconnect(self) -> None:
        """Ngắt kết nối database"""
        try:
            await self.db.disconnect()
            self.logger.info("✅ Đã ngắt kết nối database")
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi ngắt kết nối: {e}")

    # ==================== MANGA SOURCE METHODS ====================

    async def get_manga_source(self, name: str) -> Optional[MangaSource]:
        """Lấy thông tin nguồn truyện theo tên"""
        try:
            return await self.db.mangasource.find_unique(where={"name": name})
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy manga source {name}: {e}")
            return None

    async def add_manga_source(
        self, name: str, base_url: str, parser_class: str, rate_limit: int = 30
    ) -> Optional[MangaSource]:
        """Thêm nguồn truyện mới"""
        try:
            return await self.db.mangasource.upsert(
                where={"name": name},
                data={
                    "create": {
                        "name": name,
                        "base_url": base_url,
                        "parser_class": parser_class,
                        "rate_limit_per_minute": rate_limit,
                    },
                    "update": {
                        "base_url": base_url,
                        "parser_class": parser_class,
                        "rate_limit_per_minute": rate_limit,
                    },
                },
            )
        except Exception as e:
            self.logger.error(f"❌ Lỗi thêm manga source {name}: {e}")
            return None

    # ==================== MANGA SERIES METHODS ====================

    async def add_manga_series(
        self,
        source_name: str,
        title: str,
        target_url: str,
        description: Optional[str] = None,
    ) -> Optional[MangaSeries]:
        """Thêm truyện mới vào hệ thống"""
        try:
            # Tìm source_id từ source_name
            source = await self.get_manga_source(source_name)
            if not source:
                raise ValueError(f"Không tìm thấy source: {source_name}")

            return await self.db.mangaseries.upsert(
                where={
                    "source_id_target_url": {
                        "source_id": source.id,
                        "target_url": target_url,
                    }
                },
                data={
                    "create": {
                        "source_id": source.id,
                        "title": title,
                        "target_url": target_url,
                        "description": description,
                    },
                    "update": {
                        "title": title,
                        "description": description,
                        "status": "ACTIVE",
                    },
                },
            )
        except Exception as e:
            self.logger.error(f"❌ Lỗi thêm manga series {title}: {e}")
            return None

    async def get_pending_series(self) -> List[MangaSeries]:
        try:
            series = await self.db.mangaseries.find_many(
                where={"status": "ACTIVE"},
                include={"source": True},
            )

            pending_series = [s for s in series if s.status != "COMPLETED"]

            self.logger.info(f"Tìm thấy {len(pending_series)} series cần xử lý")
            return pending_series

        except Exception as e:
            self.logger.error(f"Lỗi lấy pending series: {e}")
            return []

    async def reset_stuck_downloads(self):
        """Reset các chapter bị kẹt ở trạng thái DOWNLOADING"""
        try:
            stuck_chapters = await self.db.mangachapter.find_many(
                where={"download_status": "DOWNLOADING"}
            )

            reset_count = 0
            for chapter in stuck_chapters:
                await self.db.mangachapter.update(
                    where={"id": chapter.id}, data={"download_status": "PENDING"}
                )
                reset_count += 1

            if reset_count > 0:
                self.logger.info(f"🔄 Đã reset {reset_count} chapters bị kẹt")
            return reset_count

        except Exception as e:
            self.logger.error(f"❌ Lỗi reset stuck downloads: {e}")
            return 0

    async def get_series_by_id(self, series_id: int) -> Optional[MangaSeries]:
        """Lấy thông tin truyện theo ID"""
        try:
            return await self.db.mangaseries.find_unique(
                where={"id": series_id}, include={"source": True}
            )
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy series {series_id}: {e}")
            return None

    # ==================== MANGA CHAPTER METHODS ====================

    async def add_chapter(
        self, series_id: int, chapter_number: str, chapter_title: str, chapter_url: str
    ) -> Optional[MangaChapter]:
        """Thêm chapter mới vào truyện"""
        try:
            return await self.db.mangachapter.upsert(
                where={
                    "series_id_chapter_url": {
                        "series_id": series_id,
                        "chapter_url": chapter_url,
                    }
                },
                data={
                    "create": {
                        "series_id": series_id,
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title,
                        "chapter_url": chapter_url,
                    },
                    "update": {
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title,
                        "download_status": "PENDING",
                        "downloaded_at": None,
                    },
                },
            )
        except Exception as e:
            self.logger.error(f"❌ Lỗi thêm chapter {chapter_number}: {e}")
            return None

    async def update_chapter_status(
        self, chapter_id: int, status: str, image_count: Optional[int] = None
    ) -> None:
        """Cập nhật trạng thái chapter"""
        try:
            update_data: Dict[str, Any] = {"download_status": status}

            if status == "COMPLETED":
                update_data["downloaded_at"] = datetime.now()

            if image_count is not None:
                update_data["image_count"] = image_count

            await self.db.mangachapter.update(
                where={"id": chapter_id}, data=update_data
            )
            self.logger.debug(f"✅ Đã cập nhật chapter {chapter_id} -> {status}")

        except Exception as e:
            self.logger.error(f"❌ Lỗi cập nhật chapter {chapter_id}: {e}")

    async def get_pending_chapters(self, series_id: int) -> List[MangaChapter]:
        """Lấy danh sách chapter pending của truyện"""
        try:
            chapters = await self.db.mangachapter.find_many(
                where={
                    "series_id": series_id,
                    "download_status": {"in": ["PENDING", "FAILED", "PARTIAL"]},
                },
                order=[
                    {"chapter_number": "asc"},
                ],
            )
            return chapters or []
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy pending chapters series {series_id}: {e}")
            return []

    async def get_chapters_by_series(self, series_id: int) -> List[MangaChapter]:
        try:
            return await self.db.mangachapter.find_many(
                where={"series_id": series_id}, order=[{"chapter_number": "asc"}]
            )
        except Exception as e:
            self.logger.error(f"Lỗi lấy chapters series {series_id}: {e}")
            return []

    async def get_chapter_by_url(
        self, series_id: int, chapter_url: str
    ) -> Optional[MangaChapter]:
        """Lấy chapter theo URL để kiểm tra status"""
        try:
            return await self.db.mangachapter.find_unique(
                where={
                    "series_id_chapter_url": {
                        "series_id": series_id,
                        "chapter_url": chapter_url,
                    }
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy chapter by URL: {e}")
            return None

    # ==================== CHAPTER IMAGE METHODS ====================

    async def add_chapter_image(
        self,
        chapter_id: int,
        image_url: str,
        image_order: int,
        local_path: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Optional[ChapterImage]:
        """Thêm ảnh vào chapter"""
        try:
            return await self.db.chapterimage.upsert(
                where={
                    "chapter_id_image_order": {
                        "chapter_id": chapter_id,
                        "image_order": image_order,
                    }
                },
                data={
                    "create": {
                        "chapter_id": chapter_id,
                        "image_url": image_url,
                        "image_order": image_order,
                        "local_path": local_path,
                        "file_size": file_size,
                        "download_status": "COMPLETED" if local_path else "PENDING",
                    },
                    "update": {
                        "image_url": image_url,
                        "local_path": local_path,
                        "file_size": file_size,
                        "download_status": "COMPLETED" if local_path else "PENDING",
                    },
                },
            )
        except Exception as e:
            self.logger.error(
                f"❌ Lỗi thêm ảnh chapter {chapter_id} order {image_order}: {e}"
            )
            return None

    async def get_chapter_images(self, chapter_id: int) -> List[ChapterImage]:
        """Lấy danh sách ảnh của chapter"""
        try:
            images = await self.db.chapterimage.find_many(
                where={"chapter_id": chapter_id},
                order=[{"image_order": "asc"}],
            )
            return images or []
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy ảnh chapter {chapter_id}: {e}")
            return []

    async def delete_chapter_images(self, chapter_id: int) -> None:
        """Xóa tất cả ảnh của chapter (khi retry)"""
        try:
            await self.db.chapterimage.delete_many(where={"chapter_id": chapter_id})
            self.logger.info(f"✅ Đã xóa ảnh chapter {chapter_id}")
        except Exception as e:
            self.logger.error(f"❌ Lỗi xóa ảnh chapter {chapter_id}: {e}")
