"""
DTCG Database Updater Skill - 配置管理
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 配置
CONFIG = {
    # 日文卡牌爬虫配置
    "jp_card": {
        "enabled": True,
        "source_url": "https://digimoncard.com",
        "output_path": PROJECT_ROOT / "digimon_card_data",
        "incremental": True,  # 增量更新
        "delay": 0.5,  # 爬取延迟（秒）
        "headless": True,  # 无头模式
    },
    
    # 中文卡牌爬虫配置
    "cn_card": {
        "enabled": True,
        "source_url": "https://app.digicamoe.cn",
        "output_path": PROJECT_ROOT / "digimon_card_data_chiness",
        "incremental": True,
        "delay": 0.3,
        "headless": True,
    },
    
    # QA 爬虫配置
    "qa": {
        "enabled": True,
        "source_url": "https://digimoncard.com/rule/#qaResult_card",
        "output_path": PROJECT_ROOT / "card_game_judge" / "card_game_QA_manger",
        "languages": ["jp", "cn"],  # jp: 日文，cn: 中文
        "delay": 1.0,
        "headless": True,
    },
    
    # 数据库配置
    "database": {
        "output_path": PROJECT_ROOT / "skill" / "data",
        "rebuild_on_update": False,  # 每次更新后是否重建数据库
        "backup_before_update": True,  # 更新前是否备份
    },
    
    # 日志配置
    "logging": {
        "level": "INFO",
        "file": "updater.log",
    }
}


def get_config(key, default=None):
    """获取配置项"""
    keys = key.split(".")
    value = CONFIG
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value


def ensure_dirs():
    """确保所有输出目录存在"""
    for section in ["jp_card", "cn_card", "qa", "database"]:
        if section in CONFIG:
            path = CONFIG[section].get("output_path")
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # 打印配置
    import json
    print("当前配置:")
    print(json.dumps(CONFIG, indent=2, default=str))
