"""
RAG 系统类型定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


class DocumentType(str, Enum):
    """文档类型"""
    RULE = "rule"           # 规则书
    RULING = "ruling"       # 官方裁定
    CARD = "card"           # 卡牌数据
    QA = "qa"              # 问答对
    CASE = "case"          # 判例


class DocumentSource(str, Enum):
    """文档来源"""
    MEMORY = "memory"       # 工作区文档
    DATABASE = "database"   # 数据库
    EXTERNAL = "external"   # 外部来源


class SearchMode(str, Enum):
    """搜索模式"""
    HYBRID = "hybrid"       # 混合搜索（向量 + 关键词）
    VECTOR = "vector"       # 仅向量搜索
    KEYWORD = "keyword"     # 仅关键词搜索
    EXACT = "exact"         # 精确匹配


@dataclass
class DocumentMetadata:
    """文档元数据"""
    doc_id: str
    title: str
    doc_type: DocumentType
    source: DocumentSource
    version: Optional[str] = None
    effective_date: Optional[str] = None
    tags: List[str] = None
    card_no: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    metadata: DocumentMetadata
    score: float
    doc_type: DocumentType
    snippet: Optional[str] = None
    highlights: List[str] = None
    
    def __post_init__(self):
        if self.highlights is None:
            self.highlights = []
        # 生成摘要（如果没有提供）
        if self.snippet is None:
            self.snippet = self.content[:200] + "..." if len(self.content) > 200 else self.content


@dataclass
class ChunkConfig:
    """文档分块配置"""
    chunk_size: int = 512
    chunk_overlap: int = 128
    separators: List[str] = None
    
    def __post_init__(self):
        if self.separators is None:
            self.separators = ["\n\n", "\n", "。", "；", " ", ""]


@dataclass
class SearchConfig:
    """搜索配置"""
    max_results: int = 5
    min_score: float = 0.20  # 降低阈值从0.35到0.20
    mode: SearchMode = SearchMode.HYBRID
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    enable_rerank: bool = True
    enable_temporal_decay: bool = False
