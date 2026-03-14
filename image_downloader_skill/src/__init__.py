"""
DTCG 卡牌图片下载 Skill
"""

from .downloader import DTCGImageDownloader
from .cn_downloader import ChineseImageDownloader
from .jp_downloader import JapaneseImageDownloader

__version__ = "1.0.0"
__all__ = [
    "DTCGImageDownloader",
    "ChineseImageDownloader",
    "JapaneseImageDownloader",
]
