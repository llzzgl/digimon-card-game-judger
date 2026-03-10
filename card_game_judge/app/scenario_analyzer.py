# -*- coding: utf-8 -*-
"""
场面分析器 - 专门处理复杂场面的效果诱发和处理顺序分析
结合 RAG 检索结果进行智能场面推导
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class EffectPriority(Enum):
    """效果处理优先级"""
    PASSIVE = 1  # 被动效果（持续适用）
    TRIGGER = 2  # 诱发效果（同时触发按回合玩家优先）
    ACTIVATION = 3  # 启动效果（玩家主动使用）


@dataclass
class TriggeredEffect:
    """触发的效果"""
    card_no: str
    card_name: str
    effect_text: str
    timing: str  # 触发时机
    owner: str  # 我方/对方
    priority: EffectPriority
    order: int = 0  # 处理顺序（0 表示待定）


@dataclass
class ScenarioState:
    """场面状态"""
    turn_player: str  # 当前回合玩家
    phase: str  # 当前阶段
    battle_area: List[Dict] = field(default_factory=list)  # 战斗区数码兽
    breeding_area: List[Dict] = field(default_factory=list)  # 育成区
    security: List[Dict] = field(default_factory=list)  # 安防
    memory: int = 0  # 内存值
    triggered_effects: List[TriggeredEffect] = field(default_factory=list)  # 待处理效果


class ScenarioAnalyzer:
    """场面分析器"""
    
    # 回合玩家优先规则
    TURN_PLAYER_PRIORITY_RULE = """
    【回合玩家优先原则】
    当多个效果同时触发时，按照以下顺序处理：
    1. 回合玩家的诱发效果
    2. 非回合玩家的诱发效果
    3. 每个玩家的效果按照自己决定的顺序处理
    """
    
    # 效果处理基本规则
    EFFECT_RESOLUTION_RULES = """
    【效果处理基本规则】
    1. 被动效果持续适用，不进入连锁
    2. 诱发效果在特定时机触发，进入连锁
    3. 启动效果由玩家主动使用，进入连锁
    4. 连锁中的效果后发先至（逆序处理）
    """
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.rule_cache = {}
    
    def analyze_trigger_timing(self, scenario_text: str, retrieved_context: List[Dict]) -> Dict:
        """
        分析效果触发时机
        
        Args:
            scenario_text: 场面描述
            retrieved_context: RAG 检索到的相关文档
        
        Returns:
            触发时机分析结果
        """
        analysis = {
            "identified_triggers": [],
            "timing_conflicts": [],
            "suggested_order": [],
            "rule_references": []
        }
        
        # 从检索结果中提取相关规则
        rules = self._extract_rules_from_context(retrieved_context, ["时机", "触发", "timing", "trigger"])
        analysis["rule_references"] = rules
        
        # 识别场面中的触发事件
        triggers = self._identify_triggers(scenario_text)
        analysis["identified_triggers"] = triggers
        
        # 检测时机冲突
        if len(triggers) > 1:
            conflicts = self._detect_timing_conflicts(triggers)
            analysis["timing_conflicts"] = conflicts
            
            # 建议处理顺序
            order = self._suggest_resolution_order(triggers, rules)
            analysis["suggested_order"] = order
        
        return analysis
    
    def analyze_effect_chain(self, scenario_text: str, retrieved_context: List[Dict]) -> Dict:
        """
        分析效果连锁
        
        Args:
            scenario_text: 场面描述
            retrieved_context: RAG 检索到的相关文档
        
        Returns:
            连锁分析结果
        """
        analysis = {
            "chain_structure": [],
            "resolution_order": [],
            "special_rulings": []
        }
        
        # 识别连锁结构
        chain = self._build_chain_structure(scenario_text)
        analysis["chain_structure"] = chain
        
        # 确定处理顺序（逆序）
        if chain:
            resolution = list(reversed(chain))
            analysis["resolution_order"] = resolution
        
        # 查找特殊裁定
        special_rulings = self._find_special_rulings(retrieved_context)
        analysis["special_rulings"] = special_rulings
        
        return analysis
    
    def generate_scenario_analysis(self, query: str, retrieved_context: List[Dict]) -> str:
        """
        生成完整的场面分析报告
        
        Args:
            query: 用户问题
            retrieved_context: RAG 检索结果
        
        Returns:
            结构化的分析报告
        """
        from app.enhanced_query_processor import enhanced_query_processor
        
        # 使用增强查询处理器分析问题
        query_analysis = enhanced_query_processor.analyze_scenario(query)
        
        report_parts = []
        
        # 1. 涉及的卡牌效果
        report_parts.append(self._analyze_involved_cards(query, retrieved_context))
        
        # 2. 相关规则引用
        report_parts.append(self._cite_relevant_rules(retrieved_context, query_analysis))
        
        # 3. 效果时机分析
        if query_analysis["needs_sequence_analysis"] or query_analysis["needs_chain_analysis"]:
            report_parts.append(self._analyze_effect_timing(query, retrieved_context))
        
        # 4. 处理顺序推导
        if query_analysis["needs_sequence_analysis"]:
            report_parts.append(self._derive_resolution_order(query, retrieved_context))
        
        # 5. 场面推导
        report_parts.append(self._simulate_scenario_progression(query, retrieved_context))
        
        # 6. 结论
        report_parts.append(self._generate_conclusion(query, retrieved_context))
        
        return "\n\n".join(report_parts)
    
    def _analyze_involved_cards(self, query: str, context: List[Dict]) -> str:
        """分析涉及的卡牌效果"""
        from app.enhanced_query_processor import enhanced_query_processor
        
        card_numbers = enhanced_query_processor.extract_card_numbers(query)
        
        if not card_numbers:
            return "【涉及的卡牌】\n未检测到具体卡牌编号，进行一般规则分析。"
        
        lines = ["【涉及的卡牌】"]
        
        # 从上下文中查找卡牌信息
        for card_no in card_numbers:
            card_info = self._find_card_in_context(card_no, context)
            if card_info:
                lines.append(f"• {card_no} {card_info.get('name', '')}: {card_info.get('effect', '效果未知')[:100]}...")
            else:
                lines.append(f"• {card_no}: 需要查询完整效果文本")
        
        return "\n".join(lines)
    
    def _cite_relevant_rules(self, context: List[Dict], query_analysis: Dict) -> str:
        """引用相关规则"""
        lines = ["【相关规则】"]
        
        # 从上下文中提取规则类文档
        rule_docs = [doc for doc in context if doc.get('doc_type') == 'rule']
        
        if rule_docs:
            for i, doc in enumerate(rule_docs[:3], 1):  # 最多 3 条
                title = doc['metadata'].get('title', '未知规则')
                content = doc['content'][:200].replace('\n', ' ')
                lines.append(f"{i}. {title}: {content}...")
        else:
            lines.append("• 规则参考中未找到直接相关条款，基于一般规则分析")
        
        return "\n".join(lines)
    
    def _analyze_effect_timing(self, query: str, context: List[Dict]) -> str:
        """分析效果时机"""
        lines = ["【效果时机分析】"]
        
        # 识别时机关键词
        timing_keywords = ["登场时", "进化时", "攻击时", "消灭时", "回合开始", "回合结束"]
        found_timings = [kw for kw in timing_keywords if kw in query]
        
        if found_timings:
            lines.append(f"检测到的效果时机：{', '.join(found_timings)}")
            lines.append("这些效果在对应时机触发，需要按照回合玩家优先原则处理。")
        else:
            lines.append("未检测到明确的时机关键词，可能是被动效果或启动效果。")
        
        return "\n".join(lines)
    
    def _derive_resolution_order(self, query: str, context: List[Dict]) -> str:
        """推导处理顺序"""
        lines = ["【处理顺序】"]
        lines.append("根据回合玩家优先原则：")
        lines.append("1. 首先处理回合玩家的诱发效果")
        lines.append("2. 然后处理非回合玩家的诱发效果")
        lines.append("3. 同一玩家的效果由该玩家决定顺序")
        lines.append("")
        lines.append("具体到本场面：")
        lines.append("• 需要明确当前回合玩家")
        lines.append("• 识别各效果的触发时机是否相同")
        lines.append("• 按上述原则确定处理顺序")
        
        return "\n".join(lines)
    
    def _simulate_scenario_progression(self, query: str, context: List[Dict]) -> str:
        """场面推导"""
        lines = ["【场面推导】"]
        lines.append("逐步推导场面变化：")
        lines.append("")
        lines.append("步骤 1: 识别触发事件")
        lines.append("步骤 2: 确定处理顺序")
        lines.append("步骤 3: 依次处理效果")
        lines.append("步骤 4: 更新场面状态")
        lines.append("")
        lines.append("注意：具体推导需要完整的卡牌效果文本和规则参考。")
        
        return "\n".join(lines)
    
    def _generate_conclusion(self, query: str, context: List[Dict]) -> str:
        """生成结论"""
        lines = ["【结论】"]
        
        # 基于检索结果生成结论
        if context:
            lines.append("基于以上分析，建议如下处理：")
            lines.append("• 请根据实际卡牌效果文本确认具体处理")
            lines.append("• 如有争议，请参考官方裁定或咨询裁判")
        else:
            lines.append("由于检索到的相关信息有限，建议：")
            lines.append("• 查阅完整的卡牌效果文本")
            lines.append("• 参考官方综合规则相关章节")
            lines.append("• 在正式比赛中咨询主审裁判")
        
        return "\n".join(lines)
    
    # ========== 辅助方法 ==========
    
    def _extract_rules_from_context(self, context: List[Dict], keywords: List[str]) -> List[Dict]:
        """从上下文中提取相关规则"""
        relevant = []
        for doc in context:
            content = doc.get('content', '').lower()
            if any(kw.lower() in content for kw in keywords):
                relevant.append(doc)
        return relevant
    
    def _identify_triggers(self, text: str) -> List[Dict]:
        """识别触发事件"""
        triggers = []
        # 简化的触发事件识别
        trigger_patterns = [
            (r'登场时', "appear"),
            (r'进化时', "evolve"),
            (r'攻击时', "attack"),
            (r'消灭时', "delete"),
            (r'回合开始', "turn_start"),
            (r'回合结束', "turn_end"),
        ]
        
        for pattern, timing in trigger_patterns:
            if re.search(pattern, text):
                triggers.append({"timing": timing, "text": pattern})
        
        return triggers
    
    def _detect_timing_conflicts(self, triggers: List[Dict]) -> List[Dict]:
        """检测时机冲突"""
        conflicts = []
        timing_groups = {}
        
        for trigger in triggers:
            timing = trigger["timing"]
            if timing not in timing_groups:
                timing_groups[timing] = []
            timing_groups[timing].append(trigger)
        
        # 同一时机有多个效果 = 冲突
        for timing, group in timing_groups.items():
            if len(group) > 1:
                conflicts.append({
                    "timing": timing,
                    "effects": group,
                    "resolution": "turn_player_priority"
                })
        
        return conflicts
    
    def _suggest_resolution_order(self, triggers: List[Dict], rules: List[Dict]) -> List[Dict]:
        """建议处理顺序"""
        # 简化实现：按回合玩家优先
        ordered = []
        for i, trigger in enumerate(triggers):
            ordered.append({
                "order": i + 1,
                "trigger": trigger,
                "principle": "turn_player_priority"
            })
        return ordered
    
    def _find_card_in_context(self, card_no: str, context: List[Dict]) -> Optional[Dict]:
        """在上下文中查找卡牌信息"""
        for doc in context:
            if card_no in doc.get('content', ''):
                return {
                    "name": doc['metadata'].get('title', ''),
                    "effect": doc['content'][:200]
                }
        return None
    
    def _build_chain_structure(self, text: str) -> List[Dict]:
        """构建连锁结构"""
        # 简化实现
        return [{"chain_link": 1, "effect": "识别到的效果"}]
    
    def _find_special_rulings(self, context: List[Dict]) -> List[Dict]:
        """查找特殊裁定"""
        rulings = []
        for doc in context:
            if doc.get('doc_type') == 'ruling':
                rulings.append(doc)
        return rulings


# 单例
scenario_analyzer = ScenarioAnalyzer()
