from typing import Dict, Type
from leecher.base_parser import BaseMangaParser
import logging


class ParserFactory:
    """Factory class để tạo parser dựa trên source"""

    _parsers: Dict[str, Type[BaseMangaParser]] = {}
    _logger = logging.getLogger(__name__)

    @classmethod
    def register_parser(cls, source_name: str, parser_class: Type[BaseMangaParser]):
        """Đăng ký parser mới"""
        cls._parsers[source_name] = parser_class
        cls._logger.info(f"✅ Đăng ký: {source_name} -> {parser_class.__name__}")

    @classmethod
    def create_parser(cls, source_name: str, session=None) -> BaseMangaParser:
        """Tạo parser instance"""
        if source_name not in cls._parsers:
            raise ValueError(f"Parser không tìm thấy: {source_name}")
        return cls._parsers[source_name](session)

    @classmethod
    def get_available_sources(cls) -> list:
        """Lấy danh sách source"""
        return list(cls._parsers.keys())
