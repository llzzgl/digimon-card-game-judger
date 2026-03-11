#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger - 数码宝贝卡牌裁判核心模块
提供卡牌查询、规则裁定、术语翻译等功能
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


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
        
        self._load_data()
    
    def _load_data(self):
        """加载所有数据文件"""
        # 加载卡牌数据
        cards_file = self.data_dir / "cards.json"
        if cards_file.exists():
            with open(cards_file, 'r', encoding='utf-8') as f:
                self.cards = json.load(f)
            print(f"Loaded {len(self.cards)} cards")
        
        # 加载裁定数据
        rulings_file = self.data_dir / "rulings.json"
        if rulings_file.exists():
            with open(rulings_file, 'r', encoding='utf-8') as f:
                self.rulings = json.load(f)
            print(f"Loaded {len(self.rulings)} rulings")
        
        # 加载规则书
        rules_file = self.data_dir / "rules.txt"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                self.rules = f.read()
            print(f"Loaded rules ({len(self.rules)} chars)")
        
        # 加载术语映射
        terms_file = self.data_dir / "terms.json"
        if terms_file.exists():
            with open(terms_file, 'r', encoding='utf-8') as f:
                self.terms = json.load(f)
            print(f"Loaded {len(self.terms)} term entries")
    
    def search_card(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        根据卡牌编号查询卡牌
        
        Args:
            card_no: 卡牌编号（如 "BT24-001"）
        
        Returns:
            卡牌信息字典，未找到返回 None
        """
        card_no = card_no.strip().upper()
        for card in self.cards:
            if card.get('card_no', '').upper() == card_no:
                return card
        return None
    
    def search_card_by_name(self, name: str, language: str = 'cn') -> List[Dict[str, Any]]:
        """
        根据卡牌名称搜索卡牌
        
        Args:
            name: 卡牌名称
            language: 语言 ('cn' 中文，'jp' 日文)
        
        Returns:
            匹配的卡牌列表
        """
        results = []
        name = name.strip().lower()
        
        for card in self.cards:
            if language == 'cn':
                card_name = card.get('card_name', '').lower()
            elif language == 'jp':
                card_name = card.get('card_name_jp', '').lower()
            else:
                card_name = card.get('card_name', '').lower()
            
            if name in card_name:
                results.append(card)
        
        return results
    
    def search_rulings(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索裁定
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的裁定列表
        """
        results = []
        keyword = keyword.lower()
        
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
        在规则书中搜索关键词
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            包含关键词的规则段落列表
        """
        results = []
        
        # 按行分割规则书
        lines = self.rules.split('\n')
        
        for line in lines:
            if keyword in line:
                results.append(line.strip())
        
        return results
    
    def get_rule_section(self, section: str) -> str:
        """
        获取规则书的特定章节
        
        Args:
            section: 章节编号（如 "1-2", "15-6"）
        
        Returns:
            章节内容
        """
        # 简单的章节查找逻辑
        # 实际实现可能需要更复杂的解析
        lines = self.rules.split('\n')
        
        in_section = False
        section_content = []
        
        for line in lines:
            if line.strip().startswith(section):
                in_section = True
            elif in_section and line.strip() and not line.startswith(' '):
                # 遇到新的章节标题
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
        
        # 在术语映射中查找
        for cn_term, jp_terms in self.terms.items():
            if direction == 'cn2jp':
                if term in cn_term or cn_term in term:
                    if isinstance(jp_terms, list) and jp_terms:
                        return jp_terms[0]
                    return str(jp_terms)
            elif direction == 'jp2cn':
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
