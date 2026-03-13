"""
爬虫配置文件
定义输出路径、爬虫设置等
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# ==================== 输出路径配置 ====================

# 最终输出路径（与原系统保持一致）
OUTPUT_PATHS = {
    "cards": PROJECT_ROOT / "skill" / "data" / "cards.json",       # 卡牌数据
    "rulings": PROJECT_ROOT / "skill" / "data" / "rulings.json",   # QA 裁定数据
    "digimon_mapping": PROJECT_ROOT / "digimon_data" / "digimon_name_mapping_v3.json",  # 数码兽名称映射
    "cards_cn": PROJECT_ROOT / "digimon_card_data_chiness" / "digimon_cards_cn.json",  # 中文卡牌数据
    "cards_jp": PROJECT_ROOT / "card_data_scraper_JP" / "output" / "cards.json",  # 日文卡牌数据
}

# 测试输出路径（Skill 内部测试用）
TEST_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "output"

# ==================== 爬虫设置 ====================

SCRAPER_CONFIG = {
    # 通用设置
    "default_timeout": 30,          # 默认超时时间（秒）
    "retry_times": 3,               # 重试次数
    "retry_delay": 2,               # 重试延迟（秒）
    "request_delay": 1,             # 请求间隔（秒）
    
    # 浏览器设置
    "headless": True,               # 无头模式
    "window_width": 1920,
    "window_height": 1080,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # 日文卡牌爬虫特定设置
    "jp": {
        "base_url": "https://digimoncard.com",
        "cardlist_url": "https://digimoncard.com/cards/",
        "lang": "ja",
    },
    
    # 中文卡牌爬虫特定设置
    "cn": {
        "base_url": "https://app.digicamoe.cn/search",
        "lang": "zh-CN",
    },
    
    # QA 爬虫特定设置
    "qa": {
        "jp_url": "https://digimoncard.com/rule/#qaResult_card",
        "lang": "ja",
    },
    
    # 数码兽图鉴爬虫特定设置
    "digimon": {
        "base_url": "http://digimons.net/digimon",
        "delay": 0.2,  # 请求延迟
    },
}

# ==================== 日志配置 ====================

LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": TEST_OUTPUT_PATH / "scraper.log",
}

# ==================== 数据验证配置 ====================

VALIDATION_CONFIG = {
    "cards": {
        "required_fields": ["card_no", "card_name", "card_type"],
        "optional_fields": ["card_name_ruby", "color", "level", "cost", "dp", "effect", "rarity"],
    },
    "rulings": {
        "required_fields": ["id", "question", "answer"],
        "optional_fields": ["card_no", "card_name", "category", "date"],
    },
    "digimon_mapping": {
        "key_type": "str",  # 日文名
        "value_type": "str",  # 中文名
    },
}
