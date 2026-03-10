# -*- coding: utf-8 -*-
"""
Query Processor Module - 合并基础查询处理器和增强版处理器
支持场面分析和效果处理顺序判断
"""
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class EffectInfo:
    """效果信息"""
    card_no: str  # 卡牌编号
    effect_text: str  # 效果文本
    timing: 'EffectTiming'  # 效果时机
    trigger: str  # 触发条件
    owner: str  # 所有者 (我方/对方)
    location: str  # 位置 (战斗区/育成区/安防等)


@dataclass
class ScenarioElement:
    """场面要素"""
    digimon: str  # 数码兽名称/卡号
    owner: str  # 所有者
    location: str  # 位置
    level: Optional[int] = None  # 等级
    dp: Optional[int] = None  # DP
    effects: List[str] = None  # 相关效果
    evolution_sources: List[str] = None  # 进化源


class EffectTiming(Enum):
    """效果时机类型"""
    TIMING_MAIN = "main"  # 主要阶段
    TIMING_ATTACK = "attack"  # 攻击时
    TIMING_BLOCK = "block"  # 阻挡时
    TIMING_APPEAR = "appear"  # 登场时
    TIMING_EVOLVE = "evolve"  # 进化时
    TIMING_DELETE = "delete"  # 消灭时
    TIMING_TURN_START = "turn_start"  # 回合开始时
    TIMING_TURN_END = "turn_end"  # 回合结束时
    TIMING_SECURITY = "security"  # 安防判定
    TIMING_COUNTER = "counter"  # 反击
    TIMING_ACTIVATION = "activation"  # 启动效果
    TIMING_PASSIVE = "passive"  # 被动效果
    TIMING_UNKNOWN = "unknown"  # 未知


class QueryProcessor:
    """基础查询处理器 - 提取卡牌编号、数码宝贝名称等关键信息"""
    
    # 卡牌编号正则
    CARD_NO_PATTERN = re.compile(
        r'(BT-?\d{1,2}-?\d{2,3}|ST-?\d{1,2}-?\d{2,3}|EX-?\d{1,2}-?\d{2,3}|P-?\d{3}|RB-?\d{2}|LM-?\d{2})', 
        re.IGNORECASE
    )
    
    # 内存/费用相关
    MEMORY_PATTERN = re.compile(r'(\d+)\s*(?:内存|メモリー |memory)', re.IGNORECASE)
    
    # 等级相关
    LEVEL_PATTERN = re.compile(r'(?:Lv\.?|等级|レベル)\s*(\d+)', re.IGNORECASE)
    
    def normalize_card_number(self, card_no: str) -> str:
        """标准化卡牌编号格式"""
        card_no = card_no.upper().strip()
        
        # 格式 1: BT1001 -> BT01-001
        match = re.match(r'^(BT|ST|EX|RB|LM)(\d{1,2})(\d{2,3})$', card_no)
        if match:
            prefix, set_num, card_num = match.groups()
            set_num = set_num.zfill(2)
            card_num = card_num.zfill(3)
            return f"{prefix}{set_num}-{card_num}"
        
        # 格式 2: BT-1-001 -> BT01-001
        match = re.match(r'^(BT|ST|EX|RB|LM)-?(\d{1,2})-(\d{2,3})$', card_no)
        if match:
            prefix, set_num, card_num = match.groups()
            set_num = set_num.zfill(2)
            card_num = card_num.zfill(3)
            return f"{prefix}{set_num}-{card_num}"
        
        # 格式 3: P-001 (促销卡)
        match = re.match(r'^P-?(\d{1,3})$', card_no)
        if match:
            card_num = match.group(1).zfill(3)
            return f"P-{card_num}"
        
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
        """构建搜索查询列表"""
        queries = []
        analysis = self.analyze_query(query)
        
        # 1. 添加卡牌编号的精确查询
        for card_no in analysis["card_numbers"]:
            queries.append((card_no, "card"))
        
        # 2. 添加原始查询（用于规则检索）
        queries.append((query, "rule"))
        
        return queries


class EnhancedQueryProcessor(QueryProcessor):
    """增强版查询处理器 - 用于场面分析和效果处理顺序判断"""
    
    # 效果时机关键词映射
    TIMING_KEYWORDS = {
        EffectTiming.TIMING_MAIN: ["主要阶段", "メイン", "main phase", "自己的回合", "相手のターン"],
        EffectTiming.TIMING_ATTACK: ["攻击时", "アタック時", "attack", "对战中"],
        EffectTiming.TIMING_BLOCK: ["阻挡时", "ブロック時", "block"],
        EffectTiming.TIMING_APPEAR: ["登场时", "登場時", "appear", "出场"],
        EffectTiming.TIMING_EVOLVE: ["进化时", "進化時", "evolve", "进化源"],
        EffectTiming.TIMING_DELETE: ["消灭时", "消滅時", "delete", "被消灭"],
        EffectTiming.TIMING_TURN_START: ["回合开始时", "ターン開始時", "turn start"],
        EffectTiming.TIMING_TURN_END: ["回合结束时", "ターン終了時", "turn end"],
        EffectTiming.TIMING_SECURITY: ["安防", "セキュリティ", "security", "判定"],
        EffectTiming.TIMING_COUNTER: ["反击", "カウンター", "counter"],
        EffectTiming.TIMING_ACTIVATION: ["启动", "起動", "activation", "使用"],
        EffectTiming.TIMING_PASSIVE: ["被动", "常时", "passive", "持续"],
    }
    
    # 卡牌编号正则（增强版）
    CARD_NO_PATTERN = re.compile(
        r'(BT-?\d{1,2}-?\d{2,3}|ST-?\d{1,2}-?\d{2}|EX-?\d{1,2}-?\d{2,3}|'
        r'P-?\d{3}|RB-?\d{2}|LM-?\d{2}|その他 -?\d+)',
        re.IGNORECASE
    )
    
    # 数码兽名称模式
    DIGIMON_NAME_PATTERN = re.compile(
        r'([一 - 龯ァ - ン a-zA-Z]{2,}兽 [一 - 龯ァ - ン a-zA-Z]{0,2}|'
        r'[一 - 龯ァ - ン a-zA-Z]{2,}モン [一 - 龯ァ - ン a-zA-Z]{0,2})',
        re.IGNORECASE
    )
    
    # 所有者关键词
    OWNER_KEYWORDS = {
        "我方": ["我方", "自己", "自分", "my", "our"],
        "对方": ["对方", "对手", "相手", "opponent", "enemy"],
    }
    
    # 位置关键词
    LOCATION_KEYWORDS = {
        "战斗区": ["战斗区", "バトルエリア", "battle area", "场上"],
        "育成区": ["育成区", "育成エリア", "breeding area"],
        "安防": ["安防", "セキュリティ", "security"],
        "手牌": ["手牌", "手札", "hand"],
        "废弃区": ["废弃区", "トラッシュ", "trash"],
        "卡组": ["卡组", "デッキ", "deck"],
        "进化源": ["进化源", "進化元", "evolution source", "under"],
    }
    
    # 效果连锁关键词
    CHAIN_KEYWORDS = ["连锁", "连锁", "同时", "同时", "trigger", "chain", "stack"]
    
    # 处理顺序关键词
    ORDER_KEYWORDS = ["先", "后", "然后", "之后", "接着", "順番", "order", "sequence"]
    
    def __init__(self):
        super().__init__()
        self._build_timing_index()
    
    def _build_timing_index(self):
        """构建时机关键词索引"""
        self.timing_index = {}
        for timing, keywords in self.TIMING_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() not in self.timing_index:
                    self.timing_index[keyword.lower()] = []
                self.timing_index[keyword.lower()].append(timing)
    
    def detect_effect_timings(self, text: str) -> List[EffectTiming]:
        """检测文本中涉及的效果时机"""
        detected = set()
        text_lower = text.lower()
        
        for keyword, timings in self.timing_index.items():
            if keyword in text_lower:
                detected.update(timings)
        
        return list(detected) if detected else [EffectTiming.TIMING_UNKNOWN]
    
    def extract_scenario_elements(self, text: str) -> List[ScenarioElement]:
        """提取场面要素"""
        elements = []
        
        patterns = [
            r'(我方 | 自己 | 相手 | 对方)[^\n]*(BT[\d-]+|[一 - 龯ァ - ン]{2,}兽)',
            r'(BT[\d-]+)[^\n]*(战斗区 | 育成区 | 安防 | 进化源)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                elem = ScenarioElement(
                    digimon=match[1] if len(match) > 1 else match[0],
                    owner="我方" if any(k in text for k in self.OWNER_KEYWORDS["我方"]) else "对方",
                    location="战斗区",
                    effects=[],
                    evolution_sources=[]
                )
                elements.append(elem)
        
        return elements
    
    def identify_question_type(self, query: str) -> str:
        """识别问题类型"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["顺序", "先后", "处理", "连锁"]):
            return "sequence"
        elif any(kw in query_lower for kw in ["触发", "时机", "什么时候"]):
            return "timing"
        elif any(kw in query_lower for kw in ["能否", "可以", "是否"]):
            return "ruling"
        elif any(kw in query_lower for kw in ["效果", "作用", "做什么"]):
            return "effect"
        else:
            return "general"
    
    def extract_key_concepts(self, query: str) -> Dict[str, List[str]]:
        """提取关键概念"""
        concepts = {
            "card_numbers": self.extract_card_numbers(query),
            "timings": [t.value for t in self.detect_effect_timings(query)],
            "question_type": self.identify_question_type(query),
            "has_chain": any(kw in query for kw in self.CHAIN_KEYWORDS),
            "has_sequence": any(kw in query for kw in self.ORDER_KEYWORDS),
        }
        
        digimon_names = self.DIGIMON_NAME_PATTERN.findall(query)
        concepts["digimon_names"] = digimon_names
        
        return concepts
    
    def build_enhanced_queries(self, query: str) -> List[Tuple[str, str, float]]:
        """构建增强版搜索查询列表"""
        queries = []
        concepts = self.extract_key_concepts(query)
        question_type = concepts["question_type"]
        
        # 1. 原始查询（最高权重）
        queries.append((query, "general", 1.0))
        
        # 2. 卡牌编号精确查询
        for card_no in concepts["card_numbers"]:
            queries.append((card_no, "card", 1.5))
        
        # 3. 效果时机相关查询
        for timing in concepts["timings"]:
            if timing != "unknown":
                timing_query = f"{timing} 效果 处理顺序"
                queries.append((timing_query, "rule", 0.8))
        
        # 4. 根据问题类型添加特定查询
        if question_type == "sequence":
            queries.append(("效果处理顺序 回合玩家优先", "rule", 0.9))
            queries.append(("同时触发 效果 连锁", "rule", 0.8))
        elif question_type == "timing":
            queries.append(("效果触发时机 主要阶段 攻击时", "rule", 0.8))
        elif question_type == "ruling":
            queries.append(("官方裁定 规则解释", "ruling", 0.7))
        
        # 5. 数码兽名称查询
        for name in concepts["digimon_names"]:
            queries.append((name, "card", 1.2))
        
        return queries
    
    def analyze_scenario(self, query: str) -> Dict:
        """全面分析场面查询"""
        concepts = self.extract_key_concepts(query)
        
        analysis = {
            "original_query": query,
            "question_type": concepts["question_type"],
            "involved_cards": concepts["card_numbers"],
            "effect_timings": concepts["timings"],
            "needs_sequence_analysis": concepts["has_sequence"] or concepts["question_type"] == "sequence",
            "needs_chain_analysis": concepts["has_chain"],
            "search_queries": self.build_enhanced_queries(query),
            "suggested_context_types": self._suggest_context_types(concepts),
        }
        
        return analysis
    
    def _suggest_context_types(self, concepts: Dict) -> List[str]:
        """建议需要的上下文类型"""
        types = ["rule"]
        
        if concepts["card_numbers"]:
            types.append("card")
        
        if concepts["question_type"] == "ruling":
            types.append("ruling")
        
        if concepts["has_chain"] or concepts["has_sequence"]:
            types.append("case")
        
        return types


# 单例
query_processor = QueryProcessor()
enhanced_query_processor = EnhancedQueryProcessor()
