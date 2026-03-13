"""
任务模块
Translation Tasks
"""
from .rulebook_trans import RulebookTranslator
from .qa_trans import QATranslator
from .card_trans import CardTranslator

__all__ = [
    "RulebookTranslator",
    "QATranslator",
    "CardTranslator",
]
