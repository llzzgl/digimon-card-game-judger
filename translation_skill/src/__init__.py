"""
DTCG Translation Skill
数码宝贝卡牌游戏翻译技能包
"""

__version__ = "1.0.0"
__author__ = "DTCG Judger Team"

# 延迟导入以避免循环依赖
__all__ = [
    "Translator",
    "TranslationEngine",
    "OpenAIEngine",
    "GeminiEngine",
    "RulebookTranslator",
    "QATranslator",
]
