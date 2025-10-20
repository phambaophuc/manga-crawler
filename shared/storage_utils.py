from pathlib import Path

from slugify import slugify


class StorageUtils:

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 100) -> str:
        slug = slugify(
            filename,
            max_length=max_length,
            word_boundary=True,
            separator="_",
            lowercase=True,
            replacements=[],
        )

        if not slug:
            slug = "untitled"

        return slug

    @staticmethod
    def create_directory_structure(
        base_path: Path, series_title: str, chapter_number: float
    ) -> Path:
        series_slug = slugify(series_title)
        chapter_folder = base_path / series_slug / f"chapter_{chapter_number}"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        return chapter_folder

    @staticmethod
    def get_relative_path(base_path: Path, full_path: Path) -> str:
        try:
            rel_path = full_path.resolve().relative_to(base_path.resolve())
            return rel_path.as_posix()
        except ValueError:
            return full_path.resolve().as_posix()
