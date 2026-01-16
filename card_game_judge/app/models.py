from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    RULE = "rule"           # 规则手册
    RULING = "ruling"       # 官方裁定
    CASE = "case"           # 判例


class DocumentMetadata(BaseModel):
    doc_type: DocumentType
    title: str
    version: Optional[str] = None
    effective_date: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []


class DocumentUpload(BaseModel):
    metadata: DocumentMetadata
    content: Optional[str] = None  # 用于文本直接上传


class QueryRequest(BaseModel):
    question: str
    doc_types: Optional[List[DocumentType]] = None  # 限定搜索范围
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str  # LLM 的规则分析
    sources: List[dict]  # 搜索到的原始数据
    cards: List[dict] = []  # 卡牌数据（直接显示，不经过LLM）
    confidence: Optional[float] = None


class DocumentInfo(BaseModel):
    id: str
    title: str
    doc_type: DocumentType
    created_at: str
    chunk_count: int
