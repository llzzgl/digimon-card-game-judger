"""
数码兽卡牌官方QA管理模块
"""

from .scraper_faq import DigimonFAQScraper, FAQDatabase, scrape_official_faq

__all__ = [
    'DigimonFAQScraper',
    'FAQDatabase', 
    'scrape_official_faq'
]

__version__ = '1.0.0'
