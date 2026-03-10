"""
DTCG Judger - 数码宝贝卡牌游戏智能裁判系统

注意：为避免循环导入和依赖问题，请直接从子模块导入：
    from src.judger.rag import RAGManager
    from src.judger.llm import LLMService
    from src.judger.memory import MemoryManager
    from src.judger.query import QueryProcessor
"""

__version__ = "2.0.0"
__author__ = "DTCG Judger Team"

# 延迟导入，避免依赖问题
__all__ = ['judger']
