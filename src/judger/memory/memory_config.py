# -*- coding: utf-8 -*-
"""
记忆系统配置
参考 openclaw 的配置理念
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"  # 短期记忆（当前会话）
    LONG_TERM = "long_term"    # 长期记忆（持久化）
    EPISODIC = "episodic"      # 情景记忆（特定场景）
    SEMANTIC = "semantic"      # 语义记忆（规则知识）


class MemoryImportance(Enum):
    """记忆重要性"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    
    # 存储配置
    storage_path: str = "./data/memory"
    max_short_term_memories: int = 50
    max_long_term_memories: int = 1000
    
    # 记忆检索配置
    enable_memory_search: bool = True
    memory_search_top_k: int = 3
    memory_similarity_threshold: float = 0.7
    
    # 记忆总结配置
    enable_auto_summarize: bool = True
    summarize_prompt_template: str = """请总结以下问答对，提炼关键信息：

问题：{question}
答案：{answer}

请用简洁的语言总结：
1. 核心规则或裁定
2. 关键卡牌或效果
3. 适用场景

总结："""
    
    # 记忆验证配置
    require_user_confirmation: bool = True
    auto_save_threshold: float = 0.9  # 自动保存的置信度阈值
    
    # 记忆衰减配置
    enable_memory_decay: bool = True
    decay_factor: float = 0.95  # 每次未使用时的衰减系数
    min_importance_to_keep: int = 1
    
    # 嵌入模型配置
    embedding_model: str = "local"  # local, openai, etc.
    
    # 灵魂配置（系统人格）
    soul_config: dict = field(default_factory=lambda: {
        "name": "DTCG裁判助手",
        "role": "数码宝贝卡牌游戏裁判",
        "personality": "专业、严谨、友好",
        "expertise": ["规则解释", "效果裁定", "时机判断", "连锁处理"],
        "principles": [
            "基于官方规则和裁定",
            "优先使用已验证的记忆",
            "不确定时明确说明",
            "持续学习和改进"
        ]
    })


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    question: str
    answer: str
    summary: str
    memory_type: MemoryType
    importance: MemoryImportance
    
    # 元数据
    card_numbers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source_docs: List[str] = field(default_factory=list)
    
    # 统计信息
    created_at: str = ""
    last_accessed_at: str = ""
    access_count: int = 0
    confidence_score: float = 1.0
    
    # 用户反馈
    user_confirmed: bool = False
    user_feedback: Optional[str] = None
    
    # 嵌入向量（用于检索）
    embedding: Optional[List[float]] = None


# 默认配置实例
default_memory_config = MemoryConfig()
