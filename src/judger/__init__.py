"""
Judger Module - DTCG 裁判核心模块

注意：为避免循环导入和依赖问题，不在此处自动导入所有子模块
请直接从具体子模块导入：
    from src.judger.rag import RAGManager
    from src.judger.llm import LLMService
    from src.judger.memory import MemoryManager
    from src.judger.query import QueryProcessor
"""

__version__ = "1.0.0"

# 延迟导入，避免依赖问题
__all__ = ['rag', 'llm', 'memory', 'query', 'api']
