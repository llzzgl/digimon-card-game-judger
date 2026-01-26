# -*- coding: utf-8 -*-
"""
DTCG 规则微调数据收集脚本
从规则书和 Q&A 中提取问答对，生成微调训练数据

功能：
1. 从规则书提取问答对（带示例的规则、关键词效果、效果时机等）
2. 预留官方 Q&A 上传接口
3. 支持自定义问答添加
4. 导出为 JSONL 格式（适合微调）
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class QAPair:
    """问答对数据结构"""
    instruction: str
    input: str
    output: str
    source: str
    rule_id: str = ""
    card_no: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "source": self.source,
            "rule_id": self.rule_id,
            "card_no": self.card_no,
            "tags": self.tags
        }
    
    def to_finetune_format(self) -> Dict:
        """转换为微调格式"""
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output
        }


class DTCGDataCollector:
    """DTCG 微调数据收集器"""
    
    # 系统指令模板
    SYSTEM_INSTRUCTIONS = {
        "rule": "你是数码宝贝卡牌游戏(DTCG)的规则专家。请根据官方综合规则准确回答问题。",
        "keyword": "你是数码宝贝卡牌游戏(DTCG)的规则专家。请解释关键词效果的含义和使用方法。",
        "timing": "你是数码宝贝卡牌游戏(DTCG)的规则专家。请解释效果时机的触发条件和处理方式。",
        "qa": "你是数码宝贝卡牌游戏(DTCG)的官方裁定专家。请根据官方Q&A回答问题。",
        "scenario": "你是数码宝贝卡牌游戏(DTCG)的规则专家。请分析游戏场景并给出正确的处理方式。",
        "general": "你是数码宝贝卡牌游戏(DTCG)的规则专家。请准确回答关于游戏规则的问题。",
        "card": "你是数码宝贝卡牌游戏(DTCG)的卡牌数据专家。请准确回答关于卡牌信息和效果的问题。"
    }
    
    def __init__(self, output_dir: str = "training_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.rule_qa_pairs: List[QAPair] = []
        self.official_qa_pairs: List[QAPair] = []
        self.custom_qa_pairs: List[QAPair] = []
        self.card_qa_pairs: List[QAPair] = []  # 新增：卡牌数据问答
        
        # 规则书章节标题映射
        self.chapter_titles = {
            "1": "游戏概要",
            "2": "卡牌信息",
            "3": "游戏区域",
            "4": "游戏基础术语",
            "5": "游戏准备",
            "6": "游戏进行",
            "7": "登场",
            "8": "进化",
            "9": "使用",
            "10": "链接",
            "11": "攻击",
            "12": "阻挡",
            "13": "判定安防",
            "14": "对战",
            "15": "效果规则",
            "16": "关键词效果",
            "17": "规则检查",
            "18": "其他"
        }
    
    def extract_from_rulebook(self, rulebook_path: str) -> int:
        """
        从规则书中提取问答对
        """
        rulebook_path = Path(rulebook_path)
        if not rulebook_path.exists():
            print(f"❌ 规则书文件不存在: {rulebook_path}")
            return 0
        
        with open(rulebook_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extracted_count = 0
        
        # 1. 提取带示例的规则条款
        extracted_count += self._extract_rules_with_examples(content)
        
        # 2. 提取关键词效果定义
        extracted_count += self._extract_keyword_effects(content)
        
        # 3. 提取效果时机定义
        extracted_count += self._extract_effect_timings(content)
        
        # 4. 提取基础术语定义
        extracted_count += self._extract_basic_terms(content)
        
        # 5. 提取游戏流程相关规则
        extracted_count += self._extract_game_flow_rules(content)
        
        # 6. 生成综合性问答
        extracted_count += self._generate_comprehensive_qa(content)
        
        print(f"✅ 从规则书提取了 {extracted_count} 条问答对")
        return extracted_count
    
    def _extract_rules_with_examples(self, content: str) -> int:
        """提取带示例的规则条款"""
        count = 0
        
        # 匹配格式: X-X-X. 规则内容（例：示例内容）
        pattern = r'(\d+-\d+(?:-\d+)*(?:-\d+)*)\.\s*([^（\n]+)（例[：:]\s*([^）]+)）'
        matches = re.findall(pattern, content)
        
        for rule_id, rule_text, example in matches:
            rule_text = rule_text.strip()
            example = example.strip()
            chapter = rule_id.split('-')[0]
            chapter_name = self.chapter_titles.get(chapter, "")
            
            # 问答1: 规则解释
            qa1 = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["rule"],
                input=f"请解释规则 {rule_id} 的含义，并举例说明。",
                output=f"规则 {rule_id}（{chapter_name}）：{rule_text}\n\n示例：{example}",
                source="rulebook_example",
                rule_id=rule_id,
                tags=[chapter_name, "规则解释"]
            )
            self.rule_qa_pairs.append(qa1)
            count += 1
            
            # 问答2: 场景分析
            qa2 = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["scenario"],
                input=f"场景：{example}\n\n这种情况应该如何处理？依据是什么？",
                output=f"根据规则 {rule_id}：{rule_text}\n\n因此，{example}",
                source="rulebook_scenario",
                rule_id=rule_id,
                tags=[chapter_name, "场景分析"]
            )
            self.rule_qa_pairs.append(qa2)
            count += 1
        
        return count
    
    def _extract_keyword_effects(self, content: str) -> int:
        """提取关键词效果定义"""
        count = 0
        
        # 匹配关键词效果定义
        # 格式: 16-X. ≪关键词≫ 或 16-X-1. ≪关键词≫是"..."的关键词效果
        patterns = [
            # 完整定义格式
            r'(16-\d+(?:-\d+)?)\.\s*≪([^≫]+)≫是"([^"]+)"的关键词效果',
            # 简化格式
            r'(16-\d+)\.\s*≪([^≫]+)≫\n(16-\d+-1)\.\s*≪\2≫是"([^"]+)"的关键词效果',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 3:
                    rule_id, keyword, definition = match
                elif len(match) == 4:
                    rule_id, keyword, _, definition = match
                else:
                    continue
                
                # 问答1: 关键词解释
                qa1 = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["keyword"],
                    input=f"≪{keyword}≫是什么效果？如何使用？",
                    output=f"≪{keyword}≫是「{definition}」的关键词效果。\n\n（参考规则 {rule_id}）",
                    source="keyword_effect",
                    rule_id=rule_id,
                    tags=["关键词效果", keyword]
                )
                self.rule_qa_pairs.append(qa1)
                count += 1
        
        # 提取更详细的关键词效果说明
        keyword_sections = re.findall(
            r'(16-\d+)\.\s*≪([^≫]+)≫\n((?:16-\d+-\d+\.[^\n]+\n?)+)',
            content
        )
        
        for section_id, keyword, details in keyword_sections:
            # 提取所有子规则
            sub_rules = re.findall(r'(16-\d+-\d+)\.\s*([^\n]+)', details)
            if sub_rules:
                full_explanation = f"≪{keyword}≫的详细规则：\n\n"
                for sub_id, sub_text in sub_rules:
                    full_explanation += f"• {sub_text}\n"
                
                qa = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["keyword"],
                    input=f"请详细解释≪{keyword}≫的所有规则细节。",
                    output=full_explanation.strip(),
                    source="keyword_detail",
                    rule_id=section_id,
                    tags=["关键词效果", keyword, "详细规则"]
                )
                self.rule_qa_pairs.append(qa)
                count += 1
        
        return count
    
    def _extract_effect_timings(self, content: str) -> int:
        """提取效果时机定义"""
        count = 0
        
        # 匹配效果时机定义
        # 格式: 15-16-X. 【时机】效果是...
        pattern = r'(15-16-\d+(?:-\d+)?)\.\s*【([^】]+)】效果是[，,]?([^。]+)。'
        matches = re.findall(pattern, content)
        
        for rule_id, timing, definition in matches:
            qa = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["timing"],
                input=f"【{timing}】效果是什么时候触发的？如何处理？",
                output=f"【{timing}】效果是{definition}。\n\n（参考规则 {rule_id}）",
                source="effect_timing",
                rule_id=rule_id,
                tags=["效果时机", timing]
            )
            self.rule_qa_pairs.append(qa)
            count += 1
        
        return count
    
    def _extract_basic_terms(self, content: str) -> int:
        """提取基础术语定义"""
        count = 0
        
        # 提取第4章的术语定义
        term_patterns = [
            # 格式: 4-X. 术语名\n4-X-1. 定义
            r'(4-\d+)\.\s*([^\n]+)\n\1-1\.\s*"?\1?"?是指([^。]+)。',
            # 格式: 4-X-1. "术语"是指...
            r'(4-\d+-1)\.\s*"([^"]+)"是指([^。]+)。',
        ]
        
        for pattern in term_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 3:
                    rule_id, term, definition = match
                    
                    qa = QAPair(
                        instruction=self.SYSTEM_INSTRUCTIONS["general"],
                        input=f"在DTCG中，「{term}」是什么意思？",
                        output=f"「{term}」是指{definition}。\n\n（参考规则 {rule_id}）",
                        source="basic_term",
                        rule_id=rule_id,
                        tags=["基础术语", term]
                    )
                    self.rule_qa_pairs.append(qa)
                    count += 1
        
        return count
    
    def _extract_game_flow_rules(self, content: str) -> int:
        """提取游戏流程相关规则"""
        count = 0
        
        # 提取回合流程
        flow_qa = [
            {
                "input": "DTCG的回合流程是怎样的？",
                "output": "DTCG的回合按以下顺序进行：\n\n1. 活跃阶段 - 回合玩家将区域中自己所有卡牌同时变为活跃状态\n2. 抽卡阶段 - 回合玩家抽卡1张（先攻第一回合不抽卡）\n3. 育成阶段 - 可选择孵化、移动数码宝贝或不操作\n4. 主要阶段 - 可进行登场、进化、使用选项、攻击等行动\n\n当内存移动到对手方1以上时，回合结束。",
                "rule_id": "6-1"
            },
            {
                "input": "什么情况下回合会结束？",
                "output": "回合结束条件：\n\n1. 内存对手方1以上\n2. 该阶段中没有需要结算的处理\n\n满足以上两个条件时，进入回合结束时。回合结束时需要结算的处理全部消失后，回合结束，变为非回合玩家的回合。\n\n注意：如果回合结束时内存变为0以上，回合不会结束，仍处于该阶段。",
                "rule_id": "6-1-4"
            },
            {
                "input": "主要阶段可以进行哪些行动？",
                "output": "主要阶段可以按任意顺序进行任意次数以下行动：\n\n1. 登场 - 从手牌登场数码宝贝或驯兽师\n2. 进化 - 使区域中的数码宝贝进化\n3. 使用选项 - 使用手牌中的选项卡牌\n4. 链接 - 将卡牌链接到数码宝贝\n5. 攻击 - 用数码宝贝进行攻击\n6. 发动启动型效果 - 发动【主要】效果\n7. 跳过 - 宣言跳过，内存立即变为对手方3",
                "rule_id": "6-5"
            },
            {
                "input": "游戏的胜利条件是什么？",
                "output": "DTCG的胜利条件：\n\n1. 对手安防为0张时，1张以上可判定安防的数码宝贝对对手玩家的攻击成立\n2. 在对手的抽卡阶段，对手的卡组为0张且无法抽卡\n3. 通过卡牌效果使对手败北\n\n此外，玩家可以随时宣言投降，宣言投降的玩家立即败北。",
                "rule_id": "1-2"
            }
        ]
        
        for qa_data in flow_qa:
            qa = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["general"],
                input=qa_data["input"],
                output=qa_data["output"],
                source="game_flow",
                rule_id=qa_data["rule_id"],
                tags=["游戏流程"]
            )
            self.rule_qa_pairs.append(qa)
            count += 1
        
        return count
    
    def _generate_comprehensive_qa(self, content: str) -> int:
        """生成综合性问答"""
        count = 0
        
        comprehensive_qa = [
            {
                "input": "进化和登场有什么区别？",
                "output": "进化和登场的主要区别：\n\n【登场】\n• 将卡牌作为新卡牌置于区域\n• 登场的数码宝贝在该回合无法攻击（除非有≪速攻≫）\n• 支付登场费用\n\n【进化】\n• 在已有的数码宝贝上方叠加卡牌\n• 进化的数码宝贝与进化源是同一只卡牌\n• 继承进化前的显示形式（活跃/休眠）\n• 支付进化费用，并抽1张卡\n• 进化后可以攻击（如果进化前可以攻击）",
                "rule_id": "7-1,8-1"
            },
            {
                "input": "什么是进化源效果？",
                "output": "进化源效果是数码宝贝获得的、来自其进化源（下方叠加卡牌）的效果。\n\n重要规则：\n• 进化源效果由数码宝贝发动，属于数码宝贝的效果\n• 1张卡牌单独不会发动进化源效果\n• 进化源效果中的「此卡牌」指的是置于进化源的那张卡牌本身\n• 数码宝贝获得进化源效果，但不算获得了进化源效果中记载的描述",
                "rule_id": "15-3"
            },
            {
                "input": "触发型效果和即时型效果有什么区别？",
                "output": "触发型效果和即时型效果的区别：\n\n【触发型效果】\n• 满足触发条件后触发，进入发动等待状态\n• 在规则或效果处理中无法发动\n• 多个触发型效果同时触发时，按顺序逐个发动\n\n【即时型效果】\n• 满足触发条件后立即插入到原因之前发动\n• 可以在规则或效果处理中发动\n• 例如「消灭时」的即时型效果在消灭之前触发，可能阻止消灭\n\n简单说：触发型效果是「事后处理」，即时型效果是「事前插入」。",
                "rule_id": "15-8-3,15-8-5"
            },
            {
                "input": "≪贯通≫效果如何处理？",
                "output": "≪贯通≫的处理流程：\n\n1. 持有≪贯通≫的数码宝贝攻击对手数码宝贝\n2. 对战中消灭对手数码宝贝时，≪贯通≫触发\n3. 先结算因对战触发的其他效果（如【消灭时】）\n4. 在攻击结束时之前，进入判定安防流程\n5. 判定对手的安防\n\n注意事项：\n• ≪贯通≫的判定安防是强制的\n• 如果对手安防为0张，无法判定安防\n• 如果攻击中的数码宝贝不在战斗区，无法判定安防\n• 持有多个≪贯通≫时，只能判定一次安防",
                "rule_id": "16-6"
            },
            {
                "input": "数码合体是什么？如何进行？",
                "output": "数码合体是登场时的特殊规则：\n\n【条件】\n• 登场的数码宝贝卡牌持有「数码合体条件」\n• 从手牌或战斗区选择符合条件的卡牌\n\n【流程】\n1. 宣言登场并公开卡牌\n2. 在支付费用前宣言数码合体\n3. 选择要置于下方的卡牌\n4. 每置于1张卡牌，登场费用按指定数值减少\n5. 支付减少后的费用\n6. 登场完成\n\n【注意】\n• 数码合体不是强制的\n• 从战斗区选择的卡牌会离开战斗区，其进化源被废弃\n• 通过效果登场时也可以进行数码合体",
                "rule_id": "7-2"
            }
        ]
        
        for qa_data in comprehensive_qa:
            qa = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["general"],
                input=qa_data["input"],
                output=qa_data["output"],
                source="comprehensive",
                rule_id=qa_data["rule_id"],
                tags=["综合问答"]
            )
            self.rule_qa_pairs.append(qa)
            count += 1
        
        return count

    # ==================== 官方 Q&A 接口 ====================
    
    def add_official_qa(self, qa_list: List[Dict]) -> int:
        """
        添加官方 Q&A 数据
        
        Args:
            qa_list: Q&A 列表，每项格式:
                {
                    "question": "问题",
                    "answer": "答案",
                    "card_no": "相关卡牌编号（可选）",
                    "card_name": "相关卡牌名称（可选）",
                    "source": "来源（可选）",
                    "date": "日期（可选）"
                }
        
        Returns:
            添加的问答数量
        """
        added_count = 0
        for qa in qa_list:
            if not qa.get("question") or not qa.get("answer"):
                continue
            
            # 构建输出，包含卡牌信息
            output = qa["answer"]
            if qa.get("card_no"):
                output = f"【{qa.get('card_no')}】{qa.get('card_name', '')}\n\n{output}"
            
            formatted_qa = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["qa"],
                input=qa["question"],
                output=output,
                source="official_qa",
                card_no=qa.get("card_no", ""),
                tags=["官方Q&A", qa.get("source", "")]
            )
            self.official_qa_pairs.append(formatted_qa)
            added_count += 1
        
        print(f"✅ 添加了 {added_count} 条官方 Q&A")
        return added_count
    
    def load_official_qa_from_file(self, filepath: str) -> int:
        """从 JSON 文件加载官方 Q&A"""
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"⚠️ Q&A 文件不存在: {filepath}")
            return 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        return self.add_official_qa(qa_list)
    
    def upload_qa_batch(self, qa_data: List[Dict]) -> int:
        """
        批量上传 Q&A 数据（预留接口，供爬虫使用）
        
        Args:
            qa_data: Q&A 数据列表，格式同 add_official_qa
        
        Returns:
            添加的问答数量
        """
        return self.add_official_qa(qa_data)
    
    # ==================== 自定义问答 ====================
    
    def add_custom_qa(self, question: str, answer: str, 
                      instruction: str = None,
                      card_no: str = "", 
                      tags: List[str] = None) -> None:
        """添加自定义问答对"""
        qa = QAPair(
            instruction=instruction or self.SYSTEM_INSTRUCTIONS["general"],
            input=question,
            output=answer,
            source="custom",
            card_no=card_no,
            tags=tags or ["自定义"]
        )
        self.custom_qa_pairs.append(qa)
        print(f"✅ 添加自定义问答: {question[:50]}...")
    
    def add_custom_qa_batch(self, qa_list: List[Dict]) -> int:
        """批量添加自定义问答"""
        count = 0
        for qa in qa_list:
            if qa.get("question") and qa.get("answer"):
                self.add_custom_qa(
                    question=qa["question"],
                    answer=qa["answer"],
                    instruction=qa.get("instruction"),
                    card_no=qa.get("card_no", ""),
                    tags=qa.get("tags", [])
                )
                count += 1
        return count
    
    # ==================== 卡牌数据处理 ====================
    
    def load_card_data(self, card_data_path: str) -> int:
        """
        从卡牌数据文件加载并生成训练数据
        
        Args:
            card_data_path: 卡牌数据 JSON 文件路径
        
        Returns:
            生成的问答数量
        """
        card_data_path = Path(card_data_path)
        if not card_data_path.exists():
            print(f"❌ 卡牌数据文件不存在: {card_data_path}")
            return 0
        
        print(f"📥 加载卡牌数据: {card_data_path}")
        with open(card_data_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        print(f"✅ 加载了 {len(cards)} 张卡牌")
        
        count = 0
        count += self._generate_card_info_qa(cards)
        count += self._generate_card_effect_qa(cards)
        count += self._generate_card_search_qa(cards)
        count += self._generate_card_comparison_qa(cards)
        
        print(f"✅ 从卡牌数据生成了 {count} 条问答对")
        return count
    
    def _generate_card_info_qa(self, cards: List[Dict]) -> int:
        """生成卡牌基本信息问答"""
        count = 0
        
        for card in cards:
            card_no = card.get("card_no", "")
            name_cn = card.get("name_cn", "")
            name_jp = card.get("name_jp", "")
            
            if not card_no or not name_cn:
                continue
            
            # 构建卡牌完整信息
            card_info = self._format_card_info(card)
            
            # 问答1: 通过卡号查询卡牌信息
            qa1 = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["card"],
                input=f"{card_no} 是什么卡？请提供详细信息。",
                output=card_info,
                source="card_data",
                card_no=card_no,
                tags=["卡牌信息", card.get("type", "")]
            )
            self.card_qa_pairs.append(qa1)
            count += 1
            
            # 问答2: 通过卡名查询卡牌信息
            qa2 = QAPair(
                instruction=self.SYSTEM_INSTRUCTIONS["card"],
                input=f"请介绍一下「{name_cn}」这张卡。",
                output=card_info,
                source="card_data",
                card_no=card_no,
                tags=["卡牌信息", card.get("type", "")]
            )
            self.card_qa_pairs.append(qa2)
            count += 1
            
            # 如果有日文名，也生成日文名查询
            if name_jp and name_jp != name_cn:
                qa3 = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"「{name_jp}」是什么卡？",
                    output=f"「{name_jp}」的中文名是「{name_cn}」。\n\n{card_info}",
                    source="card_data",
                    card_no=card_no,
                    tags=["卡牌信息", "日文名"]
                )
                self.card_qa_pairs.append(qa3)
                count += 1
        
        return count
    
    def _generate_card_effect_qa(self, cards: List[Dict]) -> int:
        """生成卡牌效果相关问答"""
        count = 0
        
        for card in cards:
            card_no = card.get("card_no", "")
            name_cn = card.get("name_cn", "")
            effect = card.get("effect", "")
            inherited_effect = card.get("inherited_effect", "")
            security_effect = card.get("security_effect", "")
            
            if not card_no or not name_cn:
                continue
            
            # 问答1: 卡牌效果查询
            if effect:
                qa1 = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"{card_no} {name_cn} 的效果是什么？",
                    output=f"【{card_no}】{name_cn}\n\n效果：{effect}",
                    source="card_effect",
                    card_no=card_no,
                    tags=["卡牌效果"]
                )
                self.card_qa_pairs.append(qa1)
                count += 1
            
            # 问答2: 进化源效果查询
            if inherited_effect:
                qa2 = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"{card_no} {name_cn} 的进化源效果是什么？",
                    output=f"【{card_no}】{name_cn}\n\n进化源效果：{inherited_effect}",
                    source="card_effect",
                    card_no=card_no,
                    tags=["进化源效果"]
                )
                self.card_qa_pairs.append(qa2)
                count += 1
            
            # 问答3: 安防效果查询
            if security_effect:
                qa3 = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"{card_no} {name_cn} 的安防效果是什么？",
                    output=f"【{card_no}】{name_cn}\n\n安防效果：{security_effect}",
                    source="card_effect",
                    card_no=card_no,
                    tags=["安防效果"]
                )
                self.card_qa_pairs.append(qa3)
                count += 1
        
        return count
    
    def _generate_card_search_qa(self, cards: List[Dict]) -> int:
        """生成卡牌搜索相关问答"""
        count = 0
        
        # 按颜色分组
        color_groups = {}
        for card in cards:
            color = card.get("color", "")
            if color:
                if color not in color_groups:
                    color_groups[color] = []
                color_groups[color].append(card)
        
        # 按特征分组
        species_groups = {}
        for card in cards:
            species = card.get("species", "")
            if species and card.get("type") == "数码兽卡":
                for sp in species.split("/"):
                    sp = sp.strip()
                    if sp:
                        if sp not in species_groups:
                            species_groups[sp] = []
                        species_groups[sp].append(card)
        
        # 生成颜色搜索问答（采样）
        for color, color_cards in color_groups.items():
            if len(color_cards) > 5:
                # 随机采样5张卡
                import random
                sampled = random.sample(color_cards, 5)
                card_list = "\n".join([f"• {c.get('card_no')} {c.get('name_cn')}" for c in sampled])
                
                qa = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"请列举一些{color}色的卡牌。",
                    output=f"以下是一些{color}色的卡牌：\n\n{card_list}\n\n（仅列举部分示例）",
                    source="card_search",
                    tags=["卡牌搜索", f"{color}色"]
                )
                self.card_qa_pairs.append(qa)
                count += 1
        
        # 生成特征搜索问答（采样）
        for species, species_cards in species_groups.items():
            if len(species_cards) >= 3:
                import random
                sampled = random.sample(species_cards, min(3, len(species_cards)))
                card_list = "\n".join([f"• {c.get('card_no')} {c.get('name_cn')}" for c in sampled])
                
                qa = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"有哪些特征包含「{species}」的数码兽？",
                    output=f"以下是一些特征包含「{species}」的数码兽：\n\n{card_list}\n\n（仅列举部分示例）",
                    source="card_search",
                    tags=["卡牌搜索", "特征"]
                )
                self.card_qa_pairs.append(qa)
                count += 1
        
        return count
    
    def _generate_card_comparison_qa(self, cards: List[Dict]) -> int:
        """生成卡牌对比问答"""
        count = 0
        
        # 找出同名不同编号的卡牌
        name_groups = {}
        for card in cards:
            name = card.get("name_cn", "")
            if name:
                if name not in name_groups:
                    name_groups[name] = []
                name_groups[name].append(card)
        
        # 生成对比问答
        for name, same_name_cards in name_groups.items():
            if len(same_name_cards) >= 2:
                # 只对比前两张
                card1, card2 = same_name_cards[0], same_name_cards[1]
                
                comparison = f"「{name}」有多个版本：\n\n"
                comparison += f"【{card1.get('card_no')}】\n"
                comparison += f"• 颜色：{card1.get('color', '')}\n"
                comparison += f"• 等级：{card1.get('level', '')}\n"
                if card1.get('play_cost'):
                    comparison += f"• 登场费用：{card1.get('play_cost')}\n"
                if card1.get('dp'):
                    comparison += f"• DP：{card1.get('dp')}\n"
                comparison += f"• 效果：{card1.get('effect', '')[:50]}...\n\n"
                
                comparison += f"【{card2.get('card_no')}】\n"
                comparison += f"• 颜色：{card2.get('color', '')}\n"
                comparison += f"• 等级：{card2.get('level', '')}\n"
                if card2.get('play_cost'):
                    comparison += f"• 登场费用：{card2.get('play_cost')}\n"
                if card2.get('dp'):
                    comparison += f"• DP：{card2.get('dp')}\n"
                comparison += f"• 效果：{card2.get('effect', '')[:50]}...\n"
                
                qa = QAPair(
                    instruction=self.SYSTEM_INSTRUCTIONS["card"],
                    input=f"「{name}」有哪些不同版本？",
                    output=comparison,
                    source="card_comparison",
                    tags=["卡牌对比"]
                )
                self.card_qa_pairs.append(qa)
                count += 1
                
                # 只生成前10个对比
                if count >= 10:
                    break
        
        return count
    
    def _format_card_info(self, card: Dict) -> str:
        """格式化卡牌完整信息"""
        info = f"【{card.get('card_no', '')}】{card.get('name_cn', '')}"
        
        if card.get('name_jp'):
            info += f"（{card.get('name_jp')}）"
        
        info += f"\n\n• 类型：{card.get('type', '')}"
        info += f"\n• 稀有度：{card.get('rarity', '')}"
        info += f"\n• 颜色：{card.get('color', '')}"
        
        if card.get('level'):
            info += f"\n• 等级：Lv.{card.get('level')}"
        
        if card.get('form'):
            info += f"\n• 形态：{card.get('form')}"
        
        if card.get('attribute'):
            info += f"\n• 属性：{card.get('attribute')}"
        
        if card.get('species'):
            info += f"\n• 特征：{card.get('species')}"
        
        if card.get('play_cost'):
            info += f"\n• 登场费用：{card.get('play_cost')}"
        
        if card.get('dp') and card.get('dp') != '-':
            info += f"\n• DP：{card.get('dp')}"
        
        if card.get('evolution_condition'):
            info += f"\n• 进化条件：{card.get('evolution_condition')}"
        
        if card.get('effect'):
            info += f"\n\n【效果】\n{card.get('effect')}"
        
        if card.get('inherited_effect'):
            info += f"\n\n【进化源效果】\n{card.get('inherited_effect')}"
        
        if card.get('security_effect'):
            info += f"\n\n【安防效果】\n{card.get('security_effect')}"
        
        return info
    
    # ==================== 数据导出 ====================
    
    def get_all_qa_pairs(self) -> List[QAPair]:
        """获取所有问答对"""
        return self.rule_qa_pairs + self.official_qa_pairs + self.custom_qa_pairs + self.card_qa_pairs
    
    def export_jsonl(self, filename: str = None, 
                     include_metadata: bool = False) -> str:
        """
        导出为 JSONL 格式（适合微调）
        
        Args:
            filename: 输出文件名
            include_metadata: 是否包含元数据（source, rule_id等）
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dtcg_finetune_data_{timestamp}.jsonl"
        
        output_path = self.output_dir / filename
        all_qa = self.get_all_qa_pairs()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in all_qa:
                if include_metadata:
                    item = qa.to_dict()
                else:
                    item = qa.to_finetune_format()
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"✅ 导出 {len(all_qa)} 条数据到: {output_path}")
        return str(output_path)
    
    def export_json(self, filename: str = None) -> str:
        """导出为 JSON 格式（便于查看和编辑）"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dtcg_finetune_data_{timestamp}.json"
        
        output_path = self.output_dir / filename
        all_qa = self.get_all_qa_pairs()
        
        data = [qa.to_dict() for qa in all_qa]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 导出 {len(all_qa)} 条数据到: {output_path}")
        return str(output_path)
    
    def export_conversation_format(self, filename: str = None) -> str:
        """
        导出为对话格式（适合 ChatML 微调）
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dtcg_conversation_{timestamp}.jsonl"
        
        output_path = self.output_dir / filename
        all_qa = self.get_all_qa_pairs()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in all_qa:
                conversation = {
                    "conversations": [
                        {"role": "system", "content": qa.instruction},
                        {"role": "user", "content": qa.input},
                        {"role": "assistant", "content": qa.output}
                    ]
                }
                f.write(json.dumps(conversation, ensure_ascii=False) + '\n')
        
        print(f"✅ 导出 {len(all_qa)} 条对话数据到: {output_path}")
        return str(output_path)
    
    def get_statistics(self) -> Dict:
        """获取数据统计"""
        all_qa = self.get_all_qa_pairs()
        
        # 统计各来源数量
        source_counts = {}
        for qa in all_qa:
            source_counts[qa.source] = source_counts.get(qa.source, 0) + 1
        
        # 统计标签
        tag_counts = {}
        for qa in all_qa:
            for tag in qa.tags:
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "rule_qa_count": len(self.rule_qa_pairs),
            "official_qa_count": len(self.official_qa_pairs),
            "custom_qa_count": len(self.custom_qa_pairs),
            "card_qa_count": len(self.card_qa_pairs),
            "total_count": len(all_qa),
            "source_distribution": source_counts,
            "tag_distribution": tag_counts
        }
    
    def print_statistics(self):
        """打印数据统计"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 50)
        print("📊 DTCG 微调数据统计")
        print("=" * 50)
        print(f"规则书问答: {stats['rule_qa_count']}")
        print(f"官方 Q&A: {stats['official_qa_count']}")
        print(f"卡牌数据问答: {stats['card_qa_count']}")
        print(f"自定义问答: {stats['custom_qa_count']}")
        print(f"总计: {stats['total_count']}")
        
        print("\n📁 来源分布:")
        for source, count in stats['source_distribution'].items():
            print(f"   {source}: {count}")
        
        print("\n🏷️ 标签分布 (Top 10):")
        sorted_tags = sorted(stats['tag_distribution'].items(), 
                           key=lambda x: x[1], reverse=True)[:10]
        for tag, count in sorted_tags:
            print(f"   {tag}: {count}")
        print("=" * 50)


# ==================== 官方 Q&A 数据模板 ====================

def create_qa_template():
    """创建官方 Q&A 数据模板文件"""
    template = [
        {
            "question": "问题内容",
            "answer": "答案内容",
            "card_no": "BT01-001",
            "card_name": "卡牌名称",
            "source": "官方网站",
            "date": "2025-01-01"
        }
    ]
    
    template_path = Path(__file__).parent / "training_data" / "official_qa_template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 创建 Q&A 模板: {template_path}")
    return str(template_path)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DTCG 微调数据收集")
    parser.add_argument("--rulebook", type=str, 
                        default="../数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt",
                        help="规则书路径")
    parser.add_argument("--qa-file", type=str, default=None,
                        help="官方 Q&A 文件路径")
    parser.add_argument("--card-data", type=str, 
                        default="../../digimon_card_data_chiness/digimon_cards_cn.json",
                        help="卡牌数据文件路径")
    parser.add_argument("--output-dir", type=str, default="training_data",
                        help="输出目录")
    parser.add_argument("--format", type=str, default="all",
                        choices=["jsonl", "json", "conversation", "all"],
                        help="输出格式")
    parser.add_argument("--create-template", action="store_true",
                        help="创建 Q&A 模板文件")
    parser.add_argument("--no-cards", action="store_true",
                        help="不加载卡牌数据")
    
    args = parser.parse_args()
    
    # 创建模板
    if args.create_template:
        create_qa_template()
        return
    
    # 初始化收集器
    collector = DTCGDataCollector(output_dir=args.output_dir)
    
    # 1. 从规则书提取
    rulebook_path = Path(__file__).parent / args.rulebook
    if rulebook_path.exists():
        collector.extract_from_rulebook(str(rulebook_path))
    else:
        print(f"⚠️ 规则书不存在: {rulebook_path}")
    
    # 2. 加载官方 Q&A
    if args.qa_file:
        collector.load_official_qa_from_file(args.qa_file)
    else:
        # 尝试加载默认位置的 Q&A 文件
        default_qa = Path(__file__).parent / "training_data" / "official_qa.json"
        if default_qa.exists():
            collector.load_official_qa_from_file(str(default_qa))
    
    # 3. 加载卡牌数据
    if not args.no_cards:
        card_data_path = Path(__file__).parent / args.card_data
        if card_data_path.exists():
            collector.load_card_data(str(card_data_path))
        else:
            print(f"⚠️ 卡牌数据不存在: {card_data_path}")
            print(f"   提示：使用 --card-data 指定卡牌数据路径，或使用 --no-cards 跳过")
    
    # 4. 显示统计
    collector.print_statistics()
    
    # 5. 导出数据
    stats = collector.get_statistics()
    if stats['total_count'] > 0:
        if args.format in ["jsonl", "all"]:
            collector.export_jsonl("dtcg_finetune_data.jsonl")
        if args.format in ["json", "all"]:
            collector.export_json("dtcg_finetune_data.json")
        if args.format in ["conversation", "all"]:
            collector.export_conversation_format("dtcg_conversation.jsonl")
    else:
        print("⚠️ 没有数据可导出")


if __name__ == "__main__":
    main()
