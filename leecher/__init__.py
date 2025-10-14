from leecher.parser_factory import ParserFactory
from leecher.parsers.truyenqq_parser import TruyenQQParser

# Đăng ký các parser
ParserFactory.register_parser("truyenqq", TruyenQQParser)

__all__ = ["ParserFactory", "TruyenQQParser"]
