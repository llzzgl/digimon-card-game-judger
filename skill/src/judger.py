#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger - 数码宝贝卡牌裁判核心模块
提供卡牌查询、规则裁定、术语翻译等功能

性能优化：添加索引以加速查询
- card_no_index: 卡牌编号 O(1) 查询
- card_name_index: 卡牌名称倒排索引
- ruling_index: QA 裁定倒排索引

模式分离：支持提问模式和纠错模式
"""

import json
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import difflib
from datetime import datetime


class QueryMode(str, Enum):
    """查询模式枚举"""
    QUESTION = "question"       # 提问模式
    CORRECTION = "correction"   # 纠错模式


class DTCGJudger:
    """数码宝贝卡牌裁判类"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化裁判器
        
        Args:
            data_dir: 数据目录路径，默认为 skill/data 目录
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 默认路径
            self.data_dir = Path(__file__).parent.parent / "data"
        
        self.cards = []
        self.rulings = []
        self.rules = ""
        self.terms = {}
        
        # 索引数据结构
        self.card_no_index = {}
        self.card_name_index = {}
        self.ruling_index = {}
        self.rule_section_index = {}
        
        # 模糊匹配支持
        self.name_variants = {}
        
        self._load_data()
    
    def _extract_keywords(self, text: str, max_keywords: int = 50) -> List[str]:
        """
        从文本中提取关键词（优化版 - 限制关键词数量）
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量，防止索引过大
        
        Returns:
            关键词列表
        """
        keywords = []
        text = text.strip()
        text_len = len(text)
        
        # 优化：限制文本长度，避免过长文本生成过多关键词
        max_text_len = 100
        if text_len > max_text_len:
            text = text[:max_text_len]
            text_len = max_text_len
        
        # 优化：优先提取 2-3 字关键词（覆盖大部分搜索场景）
        for i in range(text_len):
            for length in [2, 3]:
                if i + length <= text_len:
                    kw = text[i:i+length]
                    # 过滤纯数字、标点（允许中文、日文、拉丁字母）
                    if kw and not kw.isdigit() and not re.match(r'^[^\u4e00-\u9fa5\u30A0-\u30FF\u3040-\u309Fa-zA-Z]+$', kw):
                        keywords.append(kw)
            
            # 优化：限制每个文本的关键词数量
            if len(keywords) >= max_keywords:
                break
        
        return keywords[:max_keywords]
    
    def _load_data(self):
        """加载所有数据文件并构建索引"""
        import time
        start_time = time.time()
        
        # 加载卡牌数据
        cards_file = self.data_dir / "cards.json"
        if cards_file.exists():
            with open(cards_file, 'r', encoding='utf-8') as f:
                self.cards = json.load(f)
            print(f"Loaded {len(self.cards)} cards")
            
            # 构建卡牌编号索引（O(1) 查询）
            self.card_no_index = {}
            for card in self.cards:
                card_no = card.get('card_no', '').upper()
                if card_no:
                    # 标准化编号
                    card_no_normalized = self.normalize_card_no(card_no)
                    self.card_no_index[card_no_normalized] = card
            print(f"Created card_no index: {len(self.card_no_index)} entries")
            
            # 构建卡牌名称索引（倒排索引 - 优化版）
            self.card_name_index = {}
            seen_cards = set()  # 用于快速检查卡牌是否已添加
            
            for card in self.cards:
                card_id = card.get('card_no', id(card))
                
                for lang in ['card_name', 'card_name_jp']:
                    name = card.get(lang, '').lower()
                    if name:
                        keywords = self._extract_keywords(name)
                        for kw in keywords:
                            if kw not in self.card_name_index:
                                self.card_name_index[kw] = []
                            
                            # 优化：使用 card_id 避免重复添加同一卡牌
                            if card_id not in seen_cards:
                                self.card_name_index[kw].append(card)
                                seen_cards.add(card_id)
            
            print(f"Created card_name index: {len(self.card_name_index)} keywords")
        
        # 加载裁定数据
        rulings_file = self.data_dir / "rulings.json"
        if rulings_file.exists():
            with open(rulings_file, 'r', encoding='utf-8') as f:
                self.rulings = json.load(f)
            print(f"Loaded {len(self.rulings)} rulings")
            
            # 构建 QA 倒排索引（优化版）
            self.ruling_index = {}
            seen_rulings = set()  # 用于快速检查裁定是否已添加
            
            for ruling in self.rulings:
                ruling_id = id(ruling)
                text = f"{ruling.get('question', '')} {ruling.get('answer', '')}".lower()
                keywords = self._extract_keywords(text)
                
                for kw in keywords:
                    if kw not in self.ruling_index:
                        self.ruling_index[kw] = []
                    
                    # 优化：使用 ruling_id 避免重复添加
                    if ruling_id not in seen_rulings:
                        self.ruling_index[kw].append(ruling)
                        seen_rulings.add(ruling_id)
            
            print(f"Created ruling index: {len(self.ruling_index)} keywords")
        
        # 加载规则书
        rules_file = self.data_dir / "rules.txt"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                self.rules = f.read()
            print(f"Loaded rules ({len(self.rules)} chars)")
            
            # 预计算规则章节索引
            self.rule_section_index = {}
            current_section = None
            for line in self.rules.split('\n'):
                if self._is_section_header(line):
                    current_section = self._parse_section_number(line)
                    if current_section:
                        self.rule_section_index[current_section] = []
                elif current_section:
                    self.rule_section_index[current_section].append(line)
            print(f"Created rule section index: {len(self.rule_section_index)} sections")
        
        # 加载术语映射
        terms_file = self.data_dir / "terms.json"
        if terms_file.exists():
            with open(terms_file, 'r', encoding='utf-8') as f:
                self.terms = json.load(f)
            print(f"Loaded {len(self.terms)} term entries")
        
        # 加载名称别名映射表（用于模糊匹配和日文→中文映射）
        aliases_file = self.data_dir / "name_aliases.json"
        if aliases_file.exists():
            with open(aliases_file, 'r', encoding='utf-8') as f:
                self.name_aliases = json.load(f)
            self.name_variants = self.name_aliases.get('variants', {})
            self.jp_to_cn_map = self.name_aliases.get('jp_to_cn', {})
            # 构建反向映射：中文→日文
            self.cn_to_jp_map = {v: k for k, v in self.jp_to_cn_map.items()}
            print(f"Loaded {len(self.name_variants)} name variants and {len(self.jp_to_cn_map)} JP→CN mappings")
        else:
            self.name_variants = {}
            self.jp_to_cn_map = {}
            self.cn_to_jp_map = {}
            print("No name aliases file found (name_aliases.json)")
        
        elapsed = time.time() - start_time
        print(f"Data loading and indexing completed in {elapsed:.2f}s")
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否为规则章节标题"""
        return bool(re.match(r'^\d+-\d+', line.strip()))
    
    def _parse_section_number(self, line: str) -> Optional[str]:
        """解析章节编号"""
        match = re.match(r'^(\d+-\d+)', line.strip())
        return match.group(1) if match else None
    
    def normalize_card_no(self, card_no: str) -> str:
        """
        标准化卡牌编号格式
        
        Args:
            card_no: 卡牌编号
        
        Returns:
            标准化后的编号
        """
        card_no = card_no.strip().upper()
        # 移除前导零：EX08 → EX8, BT01 → BT1, ST01 → ST1, P01 → P1
        card_no = re.sub(r'^(EX)0+(\d)', r'\1\2', card_no)
        card_no = re.sub(r'^(BT)0+(\d)', r'\1\2', card_no)
        card_no = re.sub(r'^(ST)0+(\d)', r'\1\2', card_no)
        card_no = re.sub(r'^(P)0+(\d)', r'\1\2', card_no)
        # 统一分隔符
        card_no = card_no.replace('_', '-')
        return card_no
    
    def search_card(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        根据卡牌编号查询卡牌 - O(1) 复杂度
        
        Args:
            card_no: 卡牌编号（如 "BT24-001"）
        
        Returns:
            卡牌信息字典，未找到返回 None
        """
        card_no = self.normalize_card_no(card_no)
        # O(1) 查询
        return self.card_no_index.get(card_no)
    
    def search_card_by_name(self, name: str, language: str = 'cn') -> List[Dict[str, Any]]:
        """
        根据卡牌名称搜索卡牌 - 使用倒排索引优化
        支持别名映射和日文→中文映射
        
        Args:
            name: 卡牌名称
            language: 语言 ('cn' 中文，'jp' 日文)
        
        Returns:
            匹配的卡牌列表
        """
        name = name.strip()
        original_name = name
        original_language = language
        
        # 1. 日文名→中文名映射
        if language == 'jp' or any('\u30A0' <= c <= '\u30FF' for c in name):
            if name in self.jp_to_cn_map:
                name = self.jp_to_cn_map[name]
                language = 'cn'
            elif name.endswith('モン'):
                if name in self.jp_to_cn_map:
                    name = self.jp_to_cn_map[name]
                    language = 'cn'
        
        # 2. 中文别名→标准名映射
        name_lower = name.lower()
        if name_lower in self.name_variants:
            name = self.name_variants[name_lower]
        
        # 3. 使用索引查询（先尝试中文名）
        name_for_search = name.lower()
        if name_for_search in self.card_name_index:
            return self.card_name_index[name_for_search]
        
        # 4. 如果中文名未找到，尝试日文名（因为卡牌数据主要是日文）
        jp_name = None
        if name in self.cn_to_jp_map:
            jp_name = self.cn_to_jp_map[name]
        elif name_lower in self.cn_to_jp_map:
            jp_name = self.cn_to_jp_map[name_lower]
        
        if jp_name and jp_name.lower() in self.card_name_index:
            return self.card_name_index[jp_name.lower()]
        
        # 5. 提取关键词搜索（同时搜索中文和日文）
        keywords = self._extract_keywords(name_lower)
        if jp_name:
            keywords.extend(self._extract_keywords(jp_name.lower()))
        
        results_set = set()
        for kw in keywords:
            if kw in self.card_name_index:
                for card in self.card_name_index[kw]:
                    card_id = card.get('card_no', id(card))
                    results_set.add(card_id)
        
        if results_set:
            results = []
            seen_ids = set()
            for card in self.cards:
                card_id = card.get('card_no', id(card))
                if card_id in results_set and card_id not in seen_ids:
                    results.append(card)
                    seen_ids.add(card_id)
            return results
        
        # 6. 回退到线性搜索
        results = []
        search_names = [name_lower]
        if jp_name:
            search_names.append(jp_name.lower())
        
        for card in self.cards:
            card_name = card.get('card_name', '').lower()
            for search_name in search_names:
                if search_name in card_name:
                    results.append(card)
                    break
        
        return results
    
    def search_card_fuzzy(self, name: str, limit: int = 5, min_ratio: float = 0.6) -> List[Dict[str, Any]]:
        """
        模糊名称搜索 - 支持简称、变体、相似度匹配
        
        Args:
            name: 卡牌名称（可以是简称或变体）
            limit: 返回结果数量限制
            min_ratio: 最小相似度阈值 (0-1)
        
        Returns:
            匹配的卡牌列表，按相似度排序
        """
        name = name.strip().lower()
        
        # 1. 精确匹配（包括变体映射）
        results = self.search_card_by_name(name)
        if results:
            return results
        
        # 2. 检查变体映射
        if name in self.name_variants:
            mapped_name = self.name_variants[name].lower()
            results = self.search_card_by_name(mapped_name)
            if results:
                return results
        
        # 3. 相似度匹配（使用 difflib）
        candidates = []
        for card_name in self.card_name_index.keys():
            ratio = difflib.SequenceMatcher(None, name, card_name).ratio()
            if ratio >= min_ratio:
                candidates.append((ratio, card_name))
        
        # 4. 按相似度排序
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        # 5. 返回最佳匹配
        results = []
        seen_ids = set()
        for ratio, card_name in candidates[:limit]:
            for card in self.card_name_index.get(card_name, []):
                card_id = card.get('card_no', id(card))
                if card_id not in seen_ids:
                    results.append(card)
                    seen_ids.add(card_id)
        
        return results
    
    def search_rulings(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索裁定 - 使用倒排索引优化
        支持日文关键词映射和别名映射
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的裁定列表
        """
        keyword = keyword.strip()
        
        # 1. 日文关键词→中文关键词映射（通用术语）
        generic_jp_cn = {
            '進化': '进化',
            '登場': '登场',
            '攻撃': '攻击',
            '進化元': '进化元',
            '手札': '手牌',
            'ゴミ箱': '垃圾区',
        }
        for jp, cn in generic_jp_cn.items():
            if jp in keyword:
                keyword = keyword.replace(jp, cn)
        
        # 2. 日文数码兽名→中文数码兽名映射
        # 检查是否包含片假名
        if any('\u30A0' <= c <= '\u30FF' for c in keyword):
            # 尝试完整匹配
            if keyword in self.jp_to_cn_map:
                keyword = self.jp_to_cn_map[keyword]
            else:
                # 尝试提取片假名部分并映射
                import re
                katakana_matches = re.findall(r'[\u30A0-\u30FF]+', keyword)
                for katakana in katakana_matches:
                    if katakana in self.jp_to_cn_map:
                        keyword = keyword.replace(katakana, self.jp_to_cn_map[katakana])
        
        keyword = keyword.lower()
        
        # 使用索引查询
        if keyword in self.ruling_index:
            return self.ruling_index[keyword]
        
        # 如果精确关键词未找到，尝试提取关键词并搜索
        keywords = self._extract_keywords(keyword)
        results_dict = {}
        for kw in keywords:
            if kw in self.ruling_index:
                for ruling in self.ruling_index[kw]:
                    ruling_id = id(ruling)
                    if ruling_id not in results_dict:
                        results_dict[ruling_id] = ruling
        
        if results_dict:
            return list(results_dict.values())
        
        # 回退到线性搜索（兼容旧数据或索引未覆盖的情况）
        results = []
        for ruling in self.rulings:
            question = ruling.get('question', '').lower()
            answer = ruling.get('answer', '').lower()
            
            if keyword in question or keyword in answer:
                results.append(ruling)
        
        return results
    
    def get_rulings_by_card(self, card_no: str) -> List[Dict[str, Any]]:
        """
        获取特定卡牌的相关裁定
        
        Args:
            card_no: 卡牌编号
        
        Returns:
            相关裁定列表
        """
        results = []
        card_no = card_no.strip().upper()
        
        for ruling in self.rulings:
            ruling_card_no = ruling.get('card_no', '').upper()
            if card_no in ruling_card_no or ruling_card_no in card_no:
                results.append(ruling)
        
        return results
    
    def search_rules(self, keyword: str) -> List[str]:
        """
        在规则书中搜索关键词 - 使用章节索引优化
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            包含关键词的规则段落列表
        """
        results = []
        
        # 规则术语别名映射
        rule_aliases = {
            '派生诱发': '派生触发',
            '激活阶段': '活跃阶段',
            '休眠': '休息',
            '同时诱发': '同时触发',
        }
        for original, alias in rule_aliases.items():
            if original in keyword:
                keyword = keyword.replace(original, alias)
        
        # 如果规则章节索引已构建，优先使用
        if self.rule_section_index:
            # 在索引中搜索
            for section, lines in self.rule_section_index.items():
                for line in lines:
                    if keyword in line:
                        results.append(line.strip())
        else:
            # 回退到线性搜索
            lines = self.rules.split('\n')
            for line in lines:
                if keyword in line:
                    results.append(line.strip())
        
        return results
    
    def get_rule_section(self, section: str) -> str:
        """
        获取规则书的特定章节 - 使用预计算索引
        
        Args:
            section: 章节编号（如 "1-2", "15-6"）
        
        Returns:
            章节内容
        """
        # 使用预计算的章节索引
        if section in self.rule_section_index:
            return '\n'.join(self.rule_section_index[section])
        
        # 回退到线性搜索
        lines = self.rules.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if line.strip().startswith(section):
                in_section = True
            elif in_section and line.strip() and not line.startswith(' '):
                if any(c.isdigit() for c in line.strip()[0:3]):
                    break
            
            if in_section:
                section_content.append(line)
        
        return '\n'.join(section_content)
    
    def translate_term(self, term: str, direction: str = 'cn2jp') -> Optional[str]:
        """
        翻译术语
        
        Args:
            term: 要翻译的术语
            direction: 翻译方向 ('cn2jp' 中文到日文，'jp2cn' 日文到中文)
        
        Returns:
            翻译结果，未找到返回 None
        """
        term = term.strip()
        
        # 优先查找精确匹配
        exact_match = None
        
        # 在术语映射中查找
        for cn_term, jp_terms in self.terms.items():
            if direction == 'cn2jp':
                # 优先精确匹配
                if term == cn_term:
                    if isinstance(jp_terms, list) and jp_terms:
                        return jp_terms[0]
                    return str(jp_terms)
                # 其次查找包含匹配
                if term in cn_term and exact_match is None:
                    if isinstance(jp_terms, list) and jp_terms:
                        exact_match = jp_terms[0]
                    else:
                        exact_match = str(jp_terms)
            elif direction == 'jp2cn':
                if isinstance(jp_terms, list):
                    for jp_term in jp_terms:
                        # 优先精确匹配
                        if term == jp_term:
                            return cn_term.split('=')[0] if '=' in cn_term else cn_term
                elif term == str(jp_terms):
                    return cn_term.split('=')[0] if '=' in cn_term else cn_term
        
        # 返回最佳匹配
        if exact_match:
            return exact_match
        
        # 最后尝试模糊匹配
        for cn_term, jp_terms in self.terms.items():
            if direction == 'jp2cn':
                if isinstance(jp_terms, list):
                    for jp_term in jp_terms:
                        if term in jp_term or jp_term in term:
                            return cn_term.split('=')[0] if '=' in cn_term else cn_term
                elif term in str(jp_terms):
                    return cn_term.split('=')[0] if '=' in cn_term else cn_term
        
        return None
    
    def get_card_count(self) -> int:
        """获取卡牌总数"""
        return len(self.cards)
    
    def get_ruling_count(self) -> int:
        """获取裁定总数"""
        return len(self.rulings)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据统计"""
        return {
            "total_cards": len(self.cards),
            "total_rulings": len(self.rulings),
            "rules_length": len(self.rules),
            "total_terms": len(self.terms)
        }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        import sys
        
        # 估算索引内存占用
        card_no_index_size = sys.getsizeof(self.card_no_index)
        card_name_index_size = sys.getsizeof(self.card_name_index)
        ruling_index_size = sys.getsizeof(self.ruling_index)
        rule_section_index_size = sys.getsizeof(self.rule_section_index)
        
        return {
            "card_no_index_entries": len(self.card_no_index),
            "card_name_index_keywords": len(self.card_name_index),
            "ruling_index_keywords": len(self.ruling_index),
            "rule_section_index_sections": len(self.rule_section_index),
            "index_memory_estimate_bytes": (
                card_no_index_size + card_name_index_size + 
                ruling_index_size + rule_section_index_size
            )
        }
    
    def process_query(self, query: str, mode: QueryMode = QueryMode.QUESTION) -> Dict[str, Any]:
        """
        处理查询 - 根据模式分发到不同处理逻辑
        
        Args:
            query: 查询文本
            mode: 查询模式（QUESTION 或 CORRECTION）
        
        Returns:
            处理结果字典
        """
        if mode == QueryMode.CORRECTION:
            return self._handle_correction(query)
        else:
            return self._handle_question(query)
    
    def _handle_question(self, query: str) -> Dict[str, Any]:
        """
        处理提问模式查询
        
        Args:
            query: 查询文本
        
        Returns:
            查询结果字典
        """
        result = {
            "mode": "question",
            "query": query,
            "cards": [],
            "rulings": [],
            "rules": [],
            "answer": ""
        }
        
        # 1. 提取卡牌编号并查询
        card_numbers = self._extract_card_numbers(query)
        if card_numbers:
            for card_no in card_numbers:
                card = self.search_card(card_no)
                if card:
                    result["cards"].append(card)
                
                # 查询相关裁定
                card_rulings = self.get_rulings_by_card(card_no)
                result["rulings"].extend(card_rulings)
        
        # 2. 搜索裁定
        rulings = self.search_rulings(query)
        for ruling in rulings:
            if ruling not in result["rulings"]:
                result["rulings"].append(ruling)
        
        # 3. 搜索规则
        rules = self.search_rules(query)
        result["rules"] = rules
        
        # 4. 生成答案（简单拼接，实际可调用 LLM）
        answer_parts = []
        if result["cards"]:
            answer_parts.append(f"找到 {len(result['cards'])} 张相关卡牌")
        if result["rulings"]:
            answer_parts.append(f"找到 {len(result['rulings'])} 条相关裁定")
        if result["rules"]:
            answer_parts.append(f"找到 {len(result['rules'])} 条相关规则")
        
        result["answer"] = "；".join(answer_parts) if answer_parts else "未找到相关信息"
        
        return result
    
    def _handle_correction(self, query: str) -> Dict[str, Any]:
        """
        处理纠错模式查询
        
        Args:
            query: 纠错查询文本
        
        Returns:
            纠错结果字典，包含纠错记录
        """
        # 解析纠错查询
        parsed = self._parse_correction_query(query)
        
        result = {
            "mode": "correction",
            "query": query,
            "correction_record": {
                "original_query": query,
                "correction": parsed.get("correction_content", query),
                "target_card": parsed.get("target_card"),
                "target_rule": parsed.get("target_rule"),
                "original_answer_ref": parsed.get("original_answer_ref"),
                "timestamp": datetime.now().isoformat(),
                "status": "pending_review"
            },
            "reference_match": None,
            "suggestion": ""
        }
        
        # 与参考数据对比验证
        if parsed.get("target_card"):
            card = self.search_card(parsed["target_card"])
            if card:
                result["reference_match"] = {
                    "card_found": True,
                    "card_name": card.get("card_name"),
                    "card_effect": card.get("effect", "")[:200]
                }
        
        if parsed.get("target_rule"):
            rule_content = self.get_rule_section(parsed["target_rule"].replace("规则 ", ""))
            if rule_content:
                result["reference_match"] = result.get("reference_match", {})
                result["reference_match"]["rule_content"] = rule_content[:300]
        
        # 生成纠正建议
        result["suggestion"] = self._generate_correction_suggestion(result)
        
        return result
    
    def _extract_card_numbers(self, text: str) -> List[str]:
        """从文本中提取卡牌编号"""
        import re
        card_pattern = r'\b([A-Z]{2,4}\d{2,3}-\d{3})\b'
        return re.findall(card_pattern, text.upper())
    
    def _parse_correction_query(self, query: str) -> dict:
        """
        解析纠错模式的查询，提取关键信息
        
        Args:
            query: 纠错查询文本
        
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
        card_numbers = self._extract_card_numbers(query)
        if card_numbers:
            result["target_card"] = card_numbers[0]
        
        # 尝试提取规则引用（如 "规则 6-2"）
        rule_pattern = r'规则\s*(\d+-\d+)'
        rule_match = re.search(rule_pattern, query)
        if rule_match:
            result["target_rule"] = f"规则 {rule_match.group(1)}"
        
        # 尝试提取答案引用（如 "原答案说..."）
        answer_patterns = [
            r'原答案 [说称] (.+?)(?:，|。|$)',
            r'之前的回答 [说称] (.+?)(?:，|。|$)',
            r'错误 [：:] (.+?)(?:，|。|$)'
        ]
        for pattern in answer_patterns:
            match = re.search(pattern, query)
            if match:
                result["original_answer_ref"] = match.group(1)
                break
        
        return result
    
    def _generate_correction_suggestion(self, correction_result: dict) -> str:
        """
        根据纠错结果生成建议
        
        Args:
            correction_result: 纠错处理结果
        
        Returns:
            建议文本
        """
        suggestions = []
        
        if correction_result.get("reference_match"):
            suggestions.append("已找到相关参考数据，建议核对后更新裁定")
        else:
            suggestions.append("未找到直接参考数据，建议人工审核")
        
        if correction_result["correction_record"].get("target_card"):
            card_no = correction_result["correction_record"]["target_card"]
            suggestions.append(f"涉及卡牌：{card_no}")
        
        if correction_result["correction_record"].get("target_rule"):
            rule = correction_result["correction_record"]["target_rule"]
            suggestions.append(f"涉及规则：{rule}")
        
        return "；".join(suggestions)


# 便捷函数
def create_judger(data_dir: Optional[str] = None) -> DTCGJudger:
    """创建裁判器实例"""
    return DTCGJudger(data_dir)


if __name__ == "__main__":
    # 测试代码
    judger = DTCGJudger()
    
    print("\n=== 数据统计 ===")
    stats = judger.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== 测试卡牌查询 ===")
    card = judger.search_card("BT24-001")
    if card:
        print(f"找到卡牌：{card.get('card_name')}")
        print(f"效果：{card.get('effect', '无')[:100]}...")
    
    print("\n=== 测试裁定查询 ===")
    rulings = judger.search_rulings("安防")
    print(f"找到 {len(rulings)} 条相关裁定")
    if rulings:
        print(f"示例：{rulings[0].get('question', '')[:100]}...")
