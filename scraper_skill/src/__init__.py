"""
Scraper Skill - 数码宝贝卡牌爬虫技能包
"""
from .card_scraper import CardScraper
from .qa_scraper import QAScraper
from .utils.jp_scraper import JapaneseCardScraper
from .utils.cn_scraper import ChineseCardScraper
from .utils.digimon_scraper import DigimonNameScraper

__version__ = "1.0.0"
__all__ = [
    "CardScraper",
    "QAScraper",
    "JapaneseCardScraper",
    "ChineseCardScraper",
    "DigimonNameScraper",
]
