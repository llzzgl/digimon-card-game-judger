"""
RAG (Retrieval-Augmented Generation) 模块

参考 OpenClaw 的实现，提供：
- 多提供商嵌入支持
- 混合搜索（向量 + 关键词）
- 分层检索策略
- 结构化 Prompt 构建
"""

from .types import (
    DocumentType,
    DocumentSource,
    DocumentMetadata,
    SearchResult,
    SearchMode,
    SearchConfig,
    ChunkConfig
)
from .embeddings import (
    EmbeddingProvider,
    create_embedding_provider
)
from .search import HybridSearchEngine
from .chunker import DocumentChunker
from .prompt_builder import PromptBuilder
from .manager import RAGManager

__all__ = [
    # Types
    'DocumentType',
    'DocumentSource',
    'DocumentMetadata',
    'SearchResult',
    'SearchMode',
    'SearchConfig',
    'ChunkConfig',
    
    # Embeddings
    'EmbeddingProvider',
    'create_embedding_provider',
    
    # Search
    'HybridSearchEngine',
    
    # Chunker
    'DocumentChunker',
    
    # Prompt Builder
    'PromptBuilder',
    
    # Manager
    'RAGManager',
]
