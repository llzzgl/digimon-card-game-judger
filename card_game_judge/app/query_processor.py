"""
查询预处理器 - 从用户问题中提取关键信息
"""
import re
from typing import List, Tuple, Dict


class QueryProcessor:
    """处理用户查询，提取卡牌编号、数码宝贝名称等关键信息"""
    
    # 卡牌编号正则：BT01-001, ST1-01, EX1-001, EX8-074, P-001, RB-01 等
    # 支持多种格式：BT1-001, BT01-001, BT1001, BT-1-001, EX8-074
    CARD_NO_PATTERN = re.compile(
        r'(BT-?\d{1,2}-?\d{2,3}|ST-?\d{1,2}-?\d{2,3}|EX-?\d{1,2}-?\d{2,3}|P-?\d{3}|RB-?\d{2}|LM-?\d{2})', 
        re.IGNORECASE
    )
    
    # 内存/费用相关
    MEMORY_PATTERN = re.compile(r'(\d+)\s*(?:内存|メモリー|memory)', re.IGNORECASE)
    
    # 等级相关
    LEVEL_PATTERN = re.compile(r'(?:Lv\.?|等级|レベル)\s*(\d+)', re.IGNORECASE)
    
    def normalize_card_number(self, card_no: str) -> str:
        """
        标准化卡牌编号格式
        
        输入示例：BT1001, BT-1-001, BT1-1, bt01-001
        输出格式：BT01-001
        """
        card_no = card_no.upper().strip()
        
        # 处理不同格式
        # 格式1: BT1001 -> BT01-001
        match = re.match(r'^(BT|ST|EX|RB|LM)(\d{1,2})(\d{2,3})$', card_no)
        if match:
            prefix, set_num, card_num = match.groups()
            set_num = set_num.zfill(2)  # 补齐到2位
            card_num = card_num.zfill(3)  # 补齐到3位
            return f"{prefix}{set_num}-{card_num}"
        
        # 格式2: BT-1-001 -> BT01-001
        match = re.match(r'^(BT|ST|EX|RB|LM)-?(\d{1,2})-(\d{2,3})$', card_no)
        if match:
            prefix, set_num, card_num = match.groups()
            set_num = set_num.zfill(2)
            card_num = card_num.zfill(3)
            return f"{prefix}{set_num}-{card_num}"
        
        # 格式3: P-001 (促销卡)
        match = re.match(r'^P-?(\d{1,3})$', card_no)
        if match:
            card_num = match.group(1).zfill(3)
            return f"P-{card_num}"
        
        # 无法识别，返回原始值
        return card_no
    
    def extract_card_numbers(self, query: str) -> List[str]:
        """提取查询中的所有卡牌编号并标准化"""
        matches = self.CARD_NO_PATTERN.findall(query)
        result = []
        seen = set()
        
        for m in matches:
            normalized = self.normalize_card_number(m)
            if normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        
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
