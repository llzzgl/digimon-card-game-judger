"""
DTCG 图片下载器配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 默认输出目录
DEFAULT_CN_OUTPUT_DIR = PROJECT_ROOT / "card_data" / "images" / "cn" / "raw"
DEFAULT_JP_OUTPUT_DIR = PROJECT_ROOT / "card_data" / "images" / "jp" / "raw"

# 日文图片配置
JP_CONFIG = {
    "base_url": "https://digimoncard.com/images/cardlist/card/",
    "version": "02",
    "extension": ".png",
    # 卡牌系列列表
    "series": [
        "EX11", "EX10", "EX09", "EX08", "EX07", "EX06", "EX05", "EX04", "EX03", "EX02", "EX01",
        "BT25", "BT24", "BT23", "BT22", "BT21", "BT20", "BT19", "BT18", "BT17", "BT16", "BT15",
        "BT14", "BT13", "BT12", "BT11", "BT10", "BT09", "BT08", "BT07", "BT06", "BT05", "BT04",
        "BT03", "BT02", "BT01", "ST23", "ST22", "ST21", "ST20", "ST19", "ST18", "ST17", "ST16",
        "ST15", "ST14", "ST13", "ST12", "ST11", "ST10", "ST09", "ST08", "ST07", "ST06", "ST05",
        "ST04", "ST03", "ST02", "ST01"
    ]
}

# 中文图片配置
CN_CONFIG = {
    "base_url": "https://app.digicamoe.cn",
    "image_cdn": "https://dtcg-wechat.moecard.cn/img/card/",
    "series": [
        "BT25", "BT24", "BT23", "BT22", "BT21", "BT20", "BT19", "BT18", "BT17", "BT16",
        "BT15", "BT14", "BT13", "BT12", "BT11", "BT10", "BT09", "BT08", "BT07", "BT06",
        "BT05", "BT04", "BT03", "BT02", "BT01", "ST23", "ST22", "ST21", "ST20"
    ]
}

# 下载配置
DOWNLOAD_CONFIG = {
    "timeout": 30,  # 请求超时时间（秒）
    "max_retries": 3,  # 最大重试次数
    "retry_delay": 2,  # 重试延迟（秒）
    "chunk_size": 8192,  # 下载块大小
}
