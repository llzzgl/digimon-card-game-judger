#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询模式定义模块

提供提问模式和纠错模式的定义、检测和处理逻辑
"""

from enum import Enum
from typing import Optional, Tuple
from pydantic import BaseModel
from datetime import datetime


class QueryMode(str, Enum):
    """查询模式枚举"""
    QUESTION = "question"       # 提问模式 - 正常卡牌/规则查询
    CORRECTION = "correction"   # 纠错模式 - 对已有裁定/答案进行纠正
    AUTO = "auto"               # 自动检测模式


# 前缀标记定义
QUESTION_PREFIXES = ['[提问]', '[问题]', '[Q]', '[问]']
CORRECTION_PREFIXES = ['[纠错]', '[纠正]', '[C]', '[错]']


class CorrectionRecord(BaseModel):
    """纠错记录数据结构"""
    original_query: str              # 原始查询
    original_answer: Optional[str] = None  # 被纠正的答案
    correction: str                  # 纠正内容
    corrected_by: Optional[str] = None   # 纠正者 ID
    timestamp: datetime              # 时间戳
    status: str = "pending_review"   # pending/approved/rejected
    reference: Optional[str] = None  # 引用依据（规则章节等）
    original_answer_id: Optional[str] = None  # 被纠正的答案 ID
    reference_match: Optional[dict] = None  # 与参考数据的匹配结果
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def detect_mode_from_query(query: str) -> Tuple[QueryMode, str]:
    """
    从查询文本中检测模式并清理前缀
    
    Args:
        query: 原始查询文本
    
    Returns:
        (检测到的模式，清理后的查询文本)
    """
    query_stripped = query.strip()
    
    # 检查纠错前缀
    for prefix in CORRECTION_PREFIXES:
        if query_stripped.startswith(prefix):
            cleaned_query = query_stripped[len(prefix):].strip()
            return QueryMode.CORRECTION, cleaned_query
    
    # 检查提问前缀
    for prefix in QUESTION_PREFIXES:
        if query_stripped.startswith(prefix):
            cleaned_query = query_stripped[len(prefix):].strip()
            return QueryMode.QUESTION, cleaned_query
    
    # 默认提问模式
    return QueryMode.QUESTION, query_stripped


def parse_correction_query(query: str) -> dict:
    """
    解析纠错模式的查询，提取关键信息
    
    Args:
        query: 纠错查询文本（已清理前缀）
    
    Returns:
        解析后的信息字典
    """
    result = {
        "correction_content": query,
        "target_card": None,
        "target_rule": None,
        "original_answer_ref": None
    }
    
    # 尝试提取卡牌编号（如 BT24-037）
    import re
    card_pattern = r'\b([A-Z]{2,4}\d{2,3}-\d{3})\b'
    card_matches = re.findall(card_pattern, query)
    if card_matches:
        result["target_card"] = card_matches[0]
    
    # 尝试提取规则引用（如 "规则 6-2"）
    rule_pattern = r'规则\s*(\d+-\d+)'
    rule_match = re.search(rule_pattern, query)
    if rule_match:
        result["target_rule"] = f"规则 {rule_match.group(1)}"
    
    # 尝试提取答案引用（如 "原答案说..."）
    # 使用 Unicode 转义序列（在 regex 中会被正确解释）
    answer_patterns = [
        r'\u539f\u7b54\u6848\u8bf4(.*?)(?:\uff0c|\u4f46|$)',  # 原答案说...（，|但 | 结束）
        r'\u539f\u7b54\u6848[\u8bf4\u79f0\u662f](.*?)(?:\uff0c|\u3002|\u4f46|$)',  # 原答案说/称/是...
        r'\u4e4b\u524d\u7684\u56de\u7b54[\u8bf4\u79f0\u662f](.*?)(?:\uff0c|\u3002|$)',  # 之前的回答...
        r'\u9519\u8bef[\uff1a:](.*?)(?:\uff0c|\u3002|$)',  # 错误：...
        r'\u8bf4(.*?)(?:\uff0c|\u3002|\u4f46|$)',  # 说...（通用匹配）
    ]
    for pattern in answer_patterns:
        match = re.search(pattern, query)
        if match:
            result["original_answer_ref"] = match.group(1).strip()
            break
    
    return result
