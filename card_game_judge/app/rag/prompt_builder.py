"""
结构化 Prompt 构建器

功能：
- 根据检索结果构建结构化 Prompt
- 区分不同类型的上下文 (规则/裁定/卡牌)
- 添加引用溯源
- 支持思维链（Chain of Thought）引导
- 支持不确定性表达指导
- 支持引用格式规范化
- 支持多步骤推理指导
"""
from typing import List, Optional, Dict
from .types import SearchResult, DocumentType


class PromptBuilder:
    """Prompt 构建器"""
    
    def __init__(self):
        """初始化 Prompt 构建器"""
        pass
    
    def build(
        self,
        query: str,
        search_results: List[SearchResult],
        card_data: Optional[List[Dict]] = None
    ) -> str:
        """
        构建结构化 Prompt
        
        Args:
            query: 用户问题
            search_results: 搜索结果
            card_data: 额外的卡牌数据
        
        Returns:
            构建好的 Prompt
        """
        # 按文档类型分组
        rules = []
        rulings = []
        cards = []
        
        for result in search_results:
            if result.doc_type == DocumentType.RULE:
                rules.append(result)
            elif result.doc_type == DocumentType.RULING:
                rulings.append(result)
            elif result.doc_type == DocumentType.CARD:
                cards.append(result)
        
        # 添加额外的卡牌数据
        if card_data:
            for card in card_data:
                cards.append(self._format_card_dict(card))
        
        # 构建 Prompt
        prompt_parts = []
        
        # 系统角色（包含思维链和推理指导）
        prompt_parts.append(self._build_system_role())
        
        # 相关规则
        if rules:
            prompt_parts.append(self._build_rules_section(rules))
        
        # 官方裁定
        if rulings:
            prompt_parts.append(self._build_rulings_section(rulings))
        
        # 涉及卡牌
        if cards:
            prompt_parts.append(self._build_cards_section(cards))
        
        # 用户问题
        prompt_parts.append(self._build_question_section(query))
        
        # 回答要求（包含引用格式和不确定性处理）
        prompt_parts.append(self._build_requirements())
        
        return "\n\n".join(prompt_parts)
    
    def _build_system_role(self) -> str:
        """构建系统角色说明（包含思维链和多步骤推理指导）"""
        return """你是数码宝贝卡牌游戏 (Digimon Card Game) 的顶级专业裁判。

## 你的职责
基于官方规则、卡牌效果和官方裁定，为玩家提供准确、权威的裁判意见。

## 信息来源优先级
1. 官方综合规则（最高权威）
2. 卡牌效果文本（具体卡牌的实际效果）
3. 官方 QA 裁定（官方对特定情况的解释）
4. 已验证的历史裁定（用户确认正确的回答）
5. 基于规则的逻辑推导

## 思维过程（Chain of Thought）

对于复杂问题，请按以下步骤思考：

### 1. 识别关键元素
- 涉及哪些卡牌？（记录卡号）
- 涉及哪些规则？（规则章节）
- 触发时机是什么？（何时、何地、由谁触发）
- 效果类型是什么？（进化、登场、攻击、防御等）

### 2. 查找相关信息
- 检索相关规则条款
- 检索官方裁定
- 获取卡牌完整效果文本
- 注意卡牌的时态（【登场时】【攻击时】【进化时】等）

### 3. 分析互动关系
- 效果触发顺序（同时触发 vs 顺序触发）
- 优先级关系（强制效果 vs 选发效果）
- 是否有特殊规则适用（如"不能"vs"可以"）
- 连锁的处理（堆叠顺序）

### 4. 得出结论
- 基于规则给出明确答案
- 说明推理过程
- 引用具体来源
- 检查是否有例外情况

## 回答质量标准

### 必须做到
✅ 给出明确的裁定结论（是/否/视情况而定）
✅ 引用具体的规则条款或卡牌编号
✅ 解释裁定的逻辑依据
✅ 使用准确的游戏术语（参考术语表）
✅ 区分"规则"和"裁定"

### 避免做
❌ 模糊不清的回答（如"可能"、"也许"）
❌ 没有依据的猜测
❌ 忽略用户的具体问题
❌ 混淆不同版本的规则"""
    
    def _build_rules_section(self, rules: List[SearchResult]) -> str:
        """构建规则部分"""
        section = ["【相关规则】"]
        
        for i, rule in enumerate(rules, 1):
            source = self._format_source(rule)
            section.append(f"{i}. {rule.content}")
            section.append(f"   来源：{source}")
        
        return "\n".join(section)
    
    def _build_rulings_section(self, rulings: List[SearchResult]) -> str:
        """构建裁定部分"""
        section = ["【官方裁定】"]
        
        for i, ruling in enumerate(rulings, 1):
            source = self._format_source(ruling)
            section.append(f"{i}. {ruling.content}")
            section.append(f"   来源：{source}")
        
        return "\n".join(section)
    
    def _build_cards_section(self, cards: List) -> str:
        """构建卡牌部分"""
        section = ["【涉及卡牌】"]
        
        for i, card in enumerate(cards, 1):
            if isinstance(card, SearchResult):
                section.append(f"{i}. {card.content}")
                if card.metadata.card_no:
                    section.append(f"   卡号：{card.metadata.card_no}")
            elif isinstance(card, str):
                section.append(f"{i}. {card}")
        
        return "\n".join(section)
    
    def _build_question_section(self, query: str) -> str:
        """构建问题部分"""
        return f"""【玩家问题】
{query}"""
    
    def _build_requirements(self) -> str:
        """构建回答要求（包含引用格式规范和不确定性处理）"""
        return """【回答要求】

## 回答模板

请按照以下格式组织回答：

```
【裁定结论】
[明确的结论，一句话概括]

【涉及卡牌】
- [卡牌名称]（[卡号]）：[效果摘要]

【规则依据】
1. [规则引用 1]
2. [规则引用 2]

【推理过程】
[逐步解释推理过程，展示思维链]

【补充说明】
[注意事项、例外情况等]

【引用来源】
- 综合规则 [章节]
- 官方 QA [编号]
- [其他来源]
```

## 引用格式规范

### 规则引用
格式：根据综合规则 [章节号]：[规则内容摘要]
示例：根据综合规则 8.1：进化时支付的费用不会退还。

### 卡牌引用
格式：[卡牌名称]（[卡牌编号]）的效果：[效果文本摘要]
示例：奥米加兽（BT5-086）的效果："【进化】从手牌支付 3 费用..."

### 裁定引用
格式：根据官方 QA [编号/关键词]：[裁定内容]
示例：根据官方 QA（连锁相关），这种情况下效果不触发。

## 不确定性处理

当遇到不确定的情况：

1. 明确说明不确定的部分
2. 提供最可能的解释和依据
3. 标注置信度（高/中/低）
4. 建议查询官方渠道

示例：
```
⚠️ 注意：关于这种情况，官方尚未发布明确裁定。
基于规则 7.3 的推导，最可能的解释是...
建议查阅最新官方 QA 或联系官方裁判团队确认。
```

## 特殊情况处理

### 规则冲突
当不同规则似乎冲突时，按以下优先级：
1. 卡牌效果 > 综合规则
2. 特殊规则 > 一般规则
3. 新规则 > 旧规则
4. 明确规则 > 隐含规则

### 语言差异
当日文/中文卡牌文本有差异时：
- 以日文原文为准
- 说明中文翻译的差异
- 提供两种版本的解释

## 其他要求
1. 基于上述规则和裁定给出准确的裁判意见
2. 如果规则或裁定有明确说明，请引用具体条款
3. 如果涉及多张卡牌的互动，请逐步分析
4. 如果信息不足以做出判断，请说明需要补充的信息
5. 使用清晰、专业的语言，避免歧义
6. 在回答末尾注明引用的来源"""
    
    def _format_source(self, result: SearchResult) -> str:
        """格式化来源信息"""
        parts = []
        
        if result.metadata.title:
            parts.append(result.metadata.title)
        
        if result.metadata.version:
            parts.append(f"版本 {result.metadata.version}")
        
        if result.metadata.source:
            parts.append(result.metadata.source.value)
        
        return " - ".join(parts) if parts else "未知来源"
    
    def _format_card_dict(self, card: Dict) -> str:
        """格式化卡牌字典为文本"""
        parts = []
        
        if card.get('card_no'):
            parts.append(f"卡牌编号：{card['card_no']}")
        if card.get('name_cn'):
            parts.append(f"中文名：{card['name_cn']}")
        if card.get('name_jp'):
            parts.append(f"日文名：{card['name_jp']}")
        if card.get('type'):
            parts.append(f"类型：{card['type']}")
        if card.get('color'):
            parts.append(f"颜色：{card['color']}")
        if card.get('level'):
            parts.append(f"等级：Lv.{card['level']}")
        if card.get('play_cost'):
            parts.append(f"登场费用：{card['play_cost']}")
        if card.get('dp') and card['dp'] != '-':
            parts.append(f"DP: {card['dp']}")
        if card.get('effect'):
            parts.append(f"效果：{card['effect']}")
        if card.get('inherited_effect'):
            parts.append(f"继承效果：{card['inherited_effect']}")
        if card.get('security_effect'):
            parts.append(f"安防效果：{card['security_effect']}")
        
        return "\n".join(parts)
    
    def build_simple(self, query: str, context: str) -> str:
        """
        构建简单 Prompt (用于快速查询)
        
        Args:
            query: 用户问题
            context: 上下文信息
        
        Returns:
            简单 Prompt
        """
        return f"""你是数码宝贝卡牌游戏的裁判助手。

【参考信息】
{context}

【问题】
{query}

请基于参考信息回答问题。"""
