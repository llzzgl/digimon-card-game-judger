"""
搜索引擎实现

支持：
- 向量搜索
- 关键词搜索（BM25）
- 混合搜索
- 重排序
- 精确匹配加成（卡牌号、规则章节）
"""
import re
from typing import List, Dict, Optional, Tuple
import numpy as np
from .types import SearchResult, SearchMode, DocumentType, SearchConfig


# 相似度权重配置（优化后）
SIMILARITY_WEIGHTS = {
    'semantic': 0.5,      # 降低语义权重
    'keyword': 0.3,       # 提高关键词权重（卡牌名称、规则术语）
    'exact_match': 0.2    # 新增精确匹配权重
}


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    arr1 = np.array(vec1)
    arr2 = np.array(vec2)
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def bm25_score(query_terms: List[str], doc_terms: List[str], 
               avg_doc_length: float, k1: float = 1.5, b: float = 0.75) -> float:
    """
    计算 BM25 分数
    
    Args:
        query_terms: 查询词列表
        doc_terms: 文档词列表
        avg_doc_length: 平均文档长度
        k1: BM25 参数
        b: BM25 参数
    """
    doc_length = len(doc_terms)
    doc_term_freq = {}
    for term in doc_terms:
        doc_term_freq[term] = doc_term_freq.get(term, 0) + 1
    
    score = 0.0
    for term in query_terms:
        if term in doc_term_freq:
            tf = doc_term_freq[term]
            # 简化的 IDF（实际应该基于整个语料库）
            idf = 1.0
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * (numerator / denominator)
    
    return score


def tokenize_chinese(text: str) -> List[str]:
    """
    简单的中文分词
    提取：汉字词、英文词、数字
    """
    # 提取连续的汉字、英文、数字
    tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|[0-9]+', text.lower())
    return tokens


def extract_keywords(query: str) -> List[str]:
    """
    提取查询关键词
    """
    # 停用词
    stop_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '什么', '怎么', '为什么', '吗', '呢', '吧', '啊'
    }
    
    tokens = tokenize_chinese(query)
    keywords = [t for t in tokens if t not in stop_words and len(t) > 1]
    return keywords


def extract_card_number(query: str) -> Optional[str]:
    """
    从查询中提取卡牌号
    
    支持的格式：
    - BT5-086
    - BT5 086
    - BT5086
    - ST1-001
    - 等类似格式
    
    Args:
        query: 用户查询文本
    
    Returns:
        提取的卡牌号（标准化格式：BT5-086），如果没有找到则返回 None
    """
    # 卡牌号模式：字母 + 数字 + 连字符/空格 + 数字
    patterns = [
        r'([A-Z]{2,}\d{1,2})[-\s]?(\d{3})',  # BT5-086, BT5 086, BT5086
        r'([A-Z]{2,}\d{1,2})[-\s]?(\d{2,3})',  # ST1-001, ST1001
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            number = match.group(2).zfill(3)  # 补齐 3 位
            return f"{prefix}-{number}"
    
    return None


def extract_rule_section(query: str) -> Optional[str]:
    """
    从查询中提取规则章节号
    
    支持的格式：
    - 规则 8.1
    - 8.1 节
    - 第 8.1 条
    - 综合规则 8.1
    
    Args:
        query: 用户查询文本
    
    Returns:
        提取的章节号（如 "8.1"），如果没有找到则返回 None
    """
    patterns = [
        r'(?:规则 | 章节 | 条 | 节)?[\s:：]?(\d+\.\d+)',  # 规则 8.1, 8.1 节
        r'(?:综合规则 | 规则)[\s:：]?(\d+)',  # 综合规则 8
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


class HybridSearchEngine:
    """混合搜索引擎"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
    
    def search_vector(
        self,
        query_embedding: List[float],
        doc_embeddings: List[Tuple[str, List[float], Dict]],
        top_k: int
    ) -> List[Tuple[str, float, Dict]]:
        """
        向量搜索
        
        Args:
            query_embedding: 查询向量
            doc_embeddings: [(doc_id, embedding, metadata), ...]
            top_k: 返回结果数
        
        Returns:
            [(doc_id, score, metadata), ...]
        """
        results = []
        for doc_id, doc_emb, metadata in doc_embeddings:
            score = cosine_similarity(query_embedding, doc_emb)
            results.append((doc_id, score, metadata))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_keyword(
        self,
        query: str,
        documents: List[Tuple[str, str, Dict]],
        top_k: int
    ) -> List[Tuple[str, float, Dict]]:
        """
        关键词搜索（BM25）
        
        Args:
            query: 查询文本
            documents: [(doc_id, content, metadata), ...]
            top_k: 返回结果数
        
        Returns:
            [(doc_id, score, metadata), ...]
        """
        query_terms = extract_keywords(query)
        if not query_terms:
            return []
        
        # 计算平均文档长度
        doc_lengths = [len(tokenize_chinese(doc[1])) for doc in documents]
        avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
        
        results = []
        for doc_id, content, metadata in documents:
            doc_terms = tokenize_chinese(content)
            score = bm25_score(query_terms, doc_terms, avg_doc_length)
            if score > 0:
                results.append((doc_id, score, metadata))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def calculate_exact_match_score(
        self,
        query: str,
        doc_id: str,
        metadata: Dict,
        content: str
    ) -> float:
        """
        计算精确匹配分数
        
        Args:
            query: 查询文本
            doc_id: 文档 ID
            metadata: 文档元数据
            content: 文档内容
        
        Returns:
            精确匹配分数（0.0-1.0）
        """
        score = 0.0
        
        # 1. 卡牌号精确匹配（最高优先级）
        query_card_no = extract_card_number(query)
        if query_card_no:
            doc_card_no = metadata.get('card_no', '')
            if doc_card_no and doc_card_no.upper() == query_card_no.upper():
                score += 0.8  # 卡牌号精确匹配权重很高
            # 部分匹配（同系列）
            elif doc_card_no and query_card_no.split('-')[0] == doc_card_no.split('-')[0]:
                score += 0.3
        
        # 2. 规则章节精确匹配
        query_rule_section = extract_rule_section(query)
        if query_rule_section:
            doc_section = metadata.get('section', '')
            if doc_section and query_rule_section in doc_section:
                score += 0.6  # 规则章节精确匹配
        
        # 3. 标题精确匹配
        query_keywords = extract_keywords(query)
        doc_title = metadata.get('title', '').lower()
        if doc_title:
            matches = sum(1 for kw in query_keywords if kw in doc_title)
            if matches > 0:
                score += 0.2 * (matches / len(query_keywords))
        
        # 限制最高分
        return min(score, 1.0)
    
    def merge_results(
        self,
        query: str,
        vector_results: List[Tuple[str, float, Dict]],
        keyword_results: List[Tuple[str, float, Dict]]
    ) -> List[Tuple[str, float, Dict]]:
        """
        合并向量和关键词搜索结果
        
        使用加权融合策略（包含精确匹配加成）
        """
        # 归一化分数
        def normalize_scores(results: List[Tuple[str, float, Dict]]) -> Dict[str, float]:
            if not results:
                return {}
            scores = [r[1] for r in results]
            max_score = max(scores) if scores else 1.0
            min_score = min(scores) if scores else 0.0
            score_range = max_score - min_score
            if score_range < 1e-10:
                return {r[0]: 1.0 for r in results}
            return {r[0]: (r[1] - min_score) / score_range for r in results}
        
        vector_scores = normalize_scores(vector_results)
        keyword_scores = normalize_scores(keyword_results)
        
        # 合并
        all_doc_ids = set(vector_scores.keys()) | set(keyword_scores.keys())
        merged = []
        
        for doc_id in all_doc_ids:
            vec_score = vector_scores.get(doc_id, 0.0)
            kw_score = keyword_scores.get(doc_id, 0.0)
            
            # 获取元数据和内容（优先从向量结果）
            metadata = None
            content = ""
            for r in vector_results:
                if r[0] == doc_id:
                    metadata = r[2]
                    content = r[2].get('content', '')
                    break
            if metadata is None:
                for r in keyword_results:
                    if r[0] == doc_id:
                        metadata = r[2]
                        content = r[2].get('content', '')
                        break
            
            if metadata:
                # 计算精确匹配分数
                exact_match_score = self.calculate_exact_match_score(
                    query, doc_id, metadata, content
                )
                
                # 加权融合（使用优化后的权重）
                final_score = (
                    SIMILARITY_WEIGHTS['semantic'] * vec_score +
                    SIMILARITY_WEIGHTS['keyword'] * kw_score +
                    SIMILARITY_WEIGHTS['exact_match'] * exact_match_score
                )
                
                merged.append((doc_id, final_score, metadata))
        
        # 按分数排序
        merged.sort(key=lambda x: x[1], reverse=True)
        return merged
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[str, float, Dict, str]]
    ) -> List[Tuple[str, float, Dict, str]]:
        """
        重排序结果
        
        基于查询词在文档中的位置和频率
        优先精确匹配（卡牌号、规则章节）
        """
        if not self.config.enable_rerank:
            return results
        
        query_terms = extract_keywords(query)
        if not query_terms:
            return results
        
        # 提取查询中的精确匹配元素
        query_card_no = extract_card_number(query)
        query_rule_section = extract_rule_section(query)
        
        reranked = []
        for doc_id, score, metadata, content in results:
            # 基础覆盖率计算
            content_lower = content.lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            coverage = matches / len(query_terms) if query_terms else 0.0
            
            # 精确匹配加成
            exact_match_bonus = 0.0
            
            # 卡牌号精确匹配 → 置顶
            if query_card_no:
                doc_card_no = metadata.get('card_no', '')
                if doc_card_no and doc_card_no.upper() == query_card_no.upper():
                    exact_match_bonus += 0.5  # 大幅加分
            
            # 规则章节精确匹配 → 次之
            if query_rule_section:
                doc_section = metadata.get('section', '')
                if doc_section and query_rule_section in doc_section:
                    exact_match_bonus += 0.3
            
            # 调整分数
            adjusted_score = score * (1.0 + 0.2 * coverage + exact_match_bonus)
            reranked.append((doc_id, adjusted_score, metadata, content))
        
        # 重新排序
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
