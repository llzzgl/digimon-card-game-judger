"""
爬虫工具模块
"""
from .jp_scraper import JapaneseCardScraper
from .cn_scraper import ChineseCardScraper
from .digimon_scraper import DigimonNameScraper

__all__ = [
    "JapaneseCardScraper",
    "ChineseCardScraper",
    "DigimonNameScraper",
]
