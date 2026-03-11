from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    RULE = "rule"           # 规则手册
    RULING = "ruling"       # 官方裁定
    CASE = "case"           # 判例


class QueryMode(str, Enum):
    """查询模式枚举"""
    QUESTION = "question"       # 提问模式 - 正常卡牌/规则查询
    CORRECTION = "correction"   # 纠错模式 - 对已有裁定/答案进行纠正
    AUTO = "auto"               # 自动检测模式


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
    mode: QueryMode = QueryMode.AUTO  # 查询模式（auto/question/correction）
    context: Optional[dict] = None  # 可选：上下文信息


class CorrectionRequest(BaseModel):
    """纠错请求模型"""
    query: str  # 纠错内容
    original_answer_id: Optional[str] = None  # 被纠正的答案 ID
    reference: Optional[str] = None  # 引用依据（规则章节等）
    corrector_id: Optional[str] = None  # 纠正者 ID


class QueryResponse(BaseModel):
    answer: str  # LLM 的规则分析
    sources: List[dict]  # 搜索到的原始数据
    cards: List[dict] = []  # 卡牌数据（直接显示，不经过 LLM）
    confidence: Optional[float] = None
    mode: Optional[str] = None  # 使用的查询模式
    correction_record: Optional[dict] = None  # 纠错记录（仅纠错模式）


class DocumentInfo(BaseModel):
    id: str
    title: str
    doc_type: DocumentType
    created_at: str
    chunk_count: int
