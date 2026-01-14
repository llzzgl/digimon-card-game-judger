"""
查询预处理器 - 从用户问题中提取关键信息
"""
import re
from typing import List, Tuple, Dict


class QueryProcessor:
    """处理用户查询，提取卡牌编号、数码宝贝名称等关键信息"""
    
    # 卡牌编号正则：BT01-001, ST1-01, EX1-001, P-001, RB-01 等
    # 不使用 \b，改用更宽松的匹配
    CARD_NO_PATTERN = re.compile(
        r'(BT-?\d{1,2}-?\d{2,3}|ST-?\d{1,2}-?\d{2}|EX-?\d{1,2}-?\d{2,3}|P-?\d{3}|RB-?\d{2}|LM-?\d{2})', 
        re.IGNORECASE
    )
    
    # 内存/费用相关
    MEMORY_PATTERN = re.compile(r'(\d+)\s*(?:内存|メモリー|memory)', re.IGNORECASE)
    
    # 等级相关
    LEVEL_PATTERN = re.compile(r'(?:Lv\.?|等级|レベル)\s*(\d+)', re.IGNORECASE)
    
    def extract_card_numbers(self, query: str) -> List[str]:
        """提取查询中的所有卡牌编号"""
        matches = self.CARD_NO_PATTERN.findall(query)
        # 标准化格式：大写，确保有连字符
        result = []
        for m in matches:
            m = m.upper()
            # 标准化为 XX00-000 格式
            # 处理 BT20079 -> BT20-079
            if re.match(r'^(BT|ST|EX|RB|LM)(\d{1,2})(\d{2,3})$', m):
                match = re.match(r'^(BT|ST|EX|RB|LM)(\d{1,2})(\d{2,3})$', m)
                m = f"{match.group(1)}{match.group(2)}-{match.group(3)}"
            # 处理 BT-20-079 -> BT20-079
            m = re.sub(r'^(BT|ST|EX|RB|LM)-(\d)', r'\1\2', m)
            result.append(m)
        return result
    
    def extract_memory_values(self, query: str) -> List[int]:
        """提取内存值"""
        matches = self.MEMORY_PATTERN.findall(query)
        return [int(m) for m in matches]
    
    def extract_levels(self, query: str) -> List[int]:
        """提取等级"""
        matches = self.LEVEL_PATTERN.findall(query)
        return [int(m) for m in matches]
    
    def analyze_query(self, query: str) -> Dict:
        """分析查询，提取所有关键信息"""
        return {
            "original_query": query,
            "card_numbers": self.extract_card_numbers(query),
            "memory_values": self.extract_memory_values(query),
            "levels": self.extract_levels(query),
        }
    
    def build_search_queries(self, query: str) -> List[Tuple[str, str]]:
        """
        构建搜索查询列表
        返回: [(查询文本, 查询类型), ...]
        """
        queries = []
        analysis = self.analyze_query(query)
        
        # 1. 添加卡牌编号的精确查询
        for card_no in analysis["card_numbers"]:
            queries.append((card_no, "card"))
        
        # 2. 添加原始查询（用于规则检索）
        queries.append((query, "rule"))
        
        return queries


# 单例
query_processor = QueryProcessor()
