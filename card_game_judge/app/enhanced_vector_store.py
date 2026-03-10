# -*- coding: utf-8 -*-
"""
增强版向量存储 - 实现分层检索策略
根据问题类型智能选择检索源，优化检索质量
"""
from typing import List, Dict, Optional, Tuple
from enum import Enum
import time


class RetrievalStrategy(Enum):
    """检索策略"""
    BROAD = "broad"  # 广泛检索（所有一种类型）
    FOCUSED = "focused"  # 聚焦检索（特定类型）
    LAYERED = "layered"  # 分层检索（按优先级）
    HYBRID = "hybrid"  # 混合检索（结合多种）


class EnhancedVectorStore:
    """增强版向量存储管理器"""
    
    def __init__(self, base_vector_store):
        """
        Args:
            base_vector_store: 基础 VectorStoreManager 实例
        """
        self.base = base_vector_store
        
        # 检索权重配置
        self.type_weights = {
            "rule": 1.0,    # 规则
            "ruling": 1.2,  # 官方裁定（更高权重）
            "case": 0.8,    # 判例
            "card": 1.5,    # 卡牌数据（精确匹配时最高）
        }
        
        # 问题类型到文档类型的映射
        self.question_type_mapping = {
            "sequence": ["rule", "ruling", "case"],  # 处理顺序问题
            "timing": ["rule", "ruling"],  # 时机判断问题
            "ruling": ["ruling", "rule"],  # 裁定判断问题
            "effect": ["rule", "card"],  # 效果解释问题
            "card": ["card"],  # 卡牌查询
            "general": ["rule", "ruling", "card"],  # 一般问题
        }
    
    def layered_search(
        self,
        query: str,
        query_analysis: Dict,
        top_k: int = 10
    ) -> List[Dict]:
        """
        分层检索 - 根据问题类型分层搜索
        
        Args:
            query: 查询文本
            query_analysis: 查询分析结果（来自 EnhancedQueryProcessor）
            top_k: 返回结果数量
        
        Returns:
            排序后的检索结果
        """
        start_time = time.time()
        question_type = query_analysis.get("question_type", "general")
        search_queries = query_analysis.get("search_queries", [(query, "general", 1.0)])
        
        all_results = []
        
        # 分层检索：按查询权重分层
        for layer_query, layer_type, weight in search_queries:
            # 确定该层需要搜索的文档类型
            doc_types = self._get_doc_types_for_query(layer_type, question_type)
            
            # 执行检索
            layer_results = self.base.search(
                query=layer_query,
                doc_types=doc_types,
                top_k=max(3, top_k // len(search_queries)),
                translate_result=True
            )
            
            # 应用权重
            for result in layer_results:
                result["layer_weight"] = weight
                result["layer_type"] = layer_type
                # 调整分数
                result["adjusted_score"] = result["score"] * weight * self.type_weights.get(result["doc_type"], 1.0)
            
            all_results.extend(layer_results)
        
        # 去重（基于内容和元数据）
        all_results = self._deduplicate_results(all_results)
        
        # 按调整后的分数排序
        all_results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        
        # 截取 top_k
        final_results = all_results[:top_k]
        
        # 记录检索日志
        elapsed = time.time() - start_time
        print(f"[分层检索] 耗时：{elapsed:.3f}s, 检索到 {len(final_results)} 条结果")
        
        return final_results
    
    def card_aware_search(
        self,
        query: str,
        card_numbers: List[str],
        top_k: int = 8
    ) -> List[Dict]:
        """
        卡牌感知检索 - 优先检索涉及的卡牌信息
        
        Args:
            query: 查询文本
            card_numbers: 涉及的卡牌编号列表
            top_k: 返回结果数量
        
        Returns:
            检索结果
        """
        all_results = []
        
        # 1. 优先检索卡牌数据（精确匹配）
        for card_no in card_numbers:
            card_results = self.base.search_by_card_number(card_no, translate_result=True)
            for result in card_results:
                result["search_type"] = "card_exact"
                result["adjusted_score"] = result["score"] * 2.0  # 精确匹配权重翻倍
            all_results.extend(card_results)
        
        # 2. 检索规则和裁定
        rule_results = self.base.search(
            query=query,
            doc_types=["rule", "ruling"],
            top_k=top_k - len(all_results),
            translate_result=True
        )
        for result in rule_results:
            result["search_type"] = "rule_semantic"
            result["adjusted_score"] = result["score"] * 1.0
        
        all_results.extend(rule_results)
        
        # 去重并排序
        all_results = self._deduplicate_results(all_results)
        all_results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        
        return all_results[:top_k]
    
    def context_aware_search(
        self,
        query: str,
        query_analysis: Dict,
        card_numbers: List[str],
        top_k: int = 12
    ) -> List[Dict]:
        """
        上下文感知检索 - 综合多种策略
        
        Args:
            query: 查询文本
            query_analysis: 查询分析结果
            card_numbers: 涉及的卡牌编号
            top_k: 返回结果数量
        
        Returns:
            检索结果
        """
        # 根据问题类型选择策略
        question_type = query_analysis.get("question_type", "general")
        
        if card_numbers and question_type in ["effect", "card"]:
            # 卡牌相关问题：使用卡牌感知检索
            return self.card_aware_search(query, card_numbers, top_k)
        elif question_type in ["sequence", "timing"]:
            # 处理顺序/时机问题：使用分层检索
            return self.layered_search(query, query_analysis, top_k)
        else:
            # 一般问题：使用分层检索
            return self.layered_search(query, query_analysis, top_k)
    
    def build_structured_context(
        self,
        search_results: List[Dict],
        query_analysis: Dict
    ) -> str:
        """
        构建结构化的检索上下文字符串
        
        Args:
            search_results: 检索结果
            query_analysis: 查询分析结果
        
        Returns:
            结构化的上下文字符串，用于 prompt 拼接
        """
        if not search_results:
            return "【检索结果】未找到相关文档。"
        
        # 按类型分组
        grouped = {
            "card": [],
            "rule": [],
            "ruling": [],
            "case": []
        }
        
        for result in search_results:
            doc_type = result.get("doc_type", "rule")
            if doc_type in grouped:
                grouped[doc_type].append(result)
        
        # 构建结构化输出
        parts = []
        
        # 1. 卡牌信息
        if grouped["card"]:
            parts.append("【卡牌信息】")
            for i, card in enumerate(grouped["card"][:5], 1):
                title = card['metadata'].get('title', '未知卡牌')
                content = card['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title}\n   {content}...")
            parts.append("")
        
        # 2. 相关规则
        if grouped["rule"]:
            parts.append("【相关规则】")
            for i, rule in enumerate(grouped["rule"][:5], 1):
                title = rule['metadata'].get('title', '未知规则')
                score = rule.get('adjusted_score', rule.get('score', 0))
                content = rule['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title} (相关度：{score:.3f})\n   {content}...")
            parts.append("")
        
        # 3. 官方裁定
        if grouped["ruling"]:
            parts.append("【官方裁定】")
            for i, ruling in enumerate(grouped["ruling"][:3], 1):
                title = ruling['metadata'].get('title', '未知裁定')
                content = ruling['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title}\n   {content}...")
            parts.append("")
        
        # 4. 参考判例
        if grouped["case"]:
            parts.append("【参考判例】")
            for i, case in enumerate(grouped["case"][:2], 1):
                title = case['metadata'].get('title', '未知判例')
                content = case['content'][:200].replace('\n', ' ')
                parts.append(f"{i}. {title}\n   {content}...")
        
        return "\n".join(parts)
    
    def _get_doc_types_for_query(self, query_type: str, question_type: str) -> List[str]:
        """根据查询类型和问题类型确定需要搜索的文档类型"""
        if query_type == "card":
            return ["card"]
        elif query_type == "rule":
            return ["rule", "ruling"]
        else:
            return self.question_type_mapping.get(question_type, ["rule", "ruling", "card"])
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重检索结果"""
        seen = set()
        unique = []
        
        for result in results:
            # 基于内容和元数据生成唯一标识
            content_hash = hash(result['content'][:100])
            metadata_key = (
                result['metadata'].get('title', ''),
                result['metadata'].get('doc_type', ''),
                result['metadata'].get('chunk_index', 0)
            )
            result_key = (content_hash, metadata_key)
            
            if result_key not in seen:
                seen.add(result_key)
                unique.append(result)
        
        return unique


def create_enhanced_vector_store(base_vector_store) -> EnhancedVectorStore:
    """创建增强版向量存储实例"""
    return EnhancedVectorStore(base_vector_store)
