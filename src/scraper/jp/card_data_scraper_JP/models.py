"""
数码宝贝卡牌数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class CardPack:
    """卡包信息"""
    pack_id: str                    # 卡包ID (category参数值，如 503035)
    pack_name: str                  # 卡包名称 (如 "ブースターパック TIME STRANGER【BT-24】")
    pack_code: str                  # 卡包代码 (如 "BT-24")
    release_date: Optional[str]     # 发售日期
    pack_url: str                   # 卡包页面URL
    card_count: int = 0             # 卡牌数量
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Card:
    """卡牌信息"""
    # 基本信息
    card_no: str                    # 卡牌编号 (如 "BT24-001")
    card_name: str                  # 卡牌名称
    card_name_ruby: Optional[str]   # 卡牌名称假名读音
    
    # 卡牌类型
    card_type: str                  # 卡牌类型 (デジモン/オプション/テイマー/デジタマ)
    color: str                      # 颜色 (赤/青/黄/緑/黒/紫/白)
    color2: Optional[str]           # 第二颜色 (双色卡)
    
    # 数值属性
    level: Optional[int]            # 等级 (Lv.3-7)
    cost: Optional[int]             # 登场费用
    dp: Optional[int]               # DP值
    digivolve_cost1: Optional[int]  # 进化费用1
    digivolve_cost2: Optional[int]  # 进化费用2
    digivolve_color1: Optional[str] # 进化颜色1
    digivolve_color2: Optional[str] # 进化颜色2
    
    # 特征信息
    form: Optional[str]             # 形态 (成長期/成熟期/完全体/究極体)
    attribute: Optional[str]        # 属性 (ワクチン/データ/ウィルス/フリー)
    digimon_type: Optional[str]     # 类型 (龍型/獣型等)
    
    # 效果文本
    effect: Optional[str]           # 效果文本
    inherited_effect: Optional[str] # 进化源效果
    security_effect: Optional[str]  # 安防效果
    
    # 稀有度和图片
    rarity: str                     # 稀有度 (C/U/R/SR/SEC等)
    image_url: Optional[str]        # 卡图URL
    parallel_id: Optional[str]      # 异画版本ID
    
    # 所属卡包
    pack_id: str                    # 所属卡包ID
    pack_name: str                  # 所属卡包名称
    
    # 元数据
    card_url: Optional[str]         # 卡牌详情页URL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# 卡包分类常量
PACK_CATEGORIES = {
    "booster": "ブースターパック",      # 补充包
    "starter": "スタートデッキ",        # 起始卡组
    "promo": "プロモーションカード",    # 宣传卡
    "extra": "エクストラブースター",    # 额外补充包
}

# 卡牌类型常量
CARD_TYPES = {
    "digimon": "デジモン",
    "option": "オプション", 
    "tamer": "テイマー",
    "digitama": "デジタマ",
}

# 颜色常量
COLORS = {
    "red": "赤",
    "blue": "青",
    "yellow": "黄",
    "green": "緑",
    "black": "黒",
    "purple": "紫",
    "white": "白",
}

# 稀有度常量
RARITIES = {
    "C": "Common",
    "U": "Uncommon",
    "R": "Rare",
    "SR": "Super Rare",
    "SEC": "Secret Rare",
    "P": "Promo",
}
