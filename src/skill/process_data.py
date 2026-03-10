#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger Skill Data Processor
Extracts and merges card data, rulings, rules, and terminology mappings
"""

import json
import os
import glob
from pathlib import Path

BASE_DIR = Path(r"D:\LLMProject\dtcg_judger")
SKILL_DIR = BASE_DIR / "skill"
DATA_DIR = SKILL_DIR / "data"

def load_json_file(filepath):
    """Load a JSON file and return its contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def save_json_file(filepath, data):
    """Save data to a JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {filepath}")

def merge_card_data():
    """Merge all card data JSON files"""
    print("Merging card data...")
    
    # Find all *_cards.json files in digimon_card_data directory
    card_files = list((BASE_DIR / "digimon_card_data").glob("*_cards.json"))
    print(f"Found {len(card_files)} card files")
    
    all_cards = []
    seen_cards = set()  # For deduplication by card_no
    
    for card_file in card_files:
        try:
            print(f"  Processing: {card_file.name.encode('utf-8').decode('utf-8', errors='ignore')}")
        except:
            print(f"  Processing: card file")
        data = load_json_file(card_file)
        if data and isinstance(data, list):
            for card in data:
                # Create unique key for deduplication
                card_key = f"{card.get('card_no', '')}-{card.get('pack_id', '')}"
                if card_key not in seen_cards and card.get('card_no'):
                    # Skip incomplete/empty cards
                    if card.get('card_type') or card.get('effect'):
                        seen_cards.add(card_key)
                        all_cards.append(card)
    
    # Also check the finetune origin_data for additional cards
    origin_cards_file = BASE_DIR / "card_game_judge" / "finetune" / "origin_data" / "cards.json"
    if origin_cards_file.exists():
        print(f"  Processing: origin cards")
        data = load_json_file(origin_cards_file)
        if data and isinstance(data, list):
            for card in data:
                card_key = f"{card.get('card_no', '')}-{card.get('url', '')}"
                if card_key not in seen_cards and card.get('card_no'):
                    seen_cards.add(card_key)
                    # Convert to standard format
                    standardized = {
                        "card_no": card.get("card_no", ""),
                        "card_name": card.get("name_cn", ""),
                        "card_name_jp": card.get("name_jp", ""),
                        "card_type": card.get("type", ""),
                        "color": card.get("color", ""),
                        "level": card.get("level", ""),
                        "cost": card.get("play_cost", ""),
                        "dp": card.get("dp", ""),
                        "form": card.get("form", ""),
                        "attribute": card.get("attribute", ""),
                        "digimon_type": card.get("species", ""),
                        "effect": card.get("effect", ""),
                        "inherited_effect": card.get("inherited_effect", ""),
                        "security_effect": card.get("security_effect", ""),
                        "rarity": card.get("rarity", ""),
                        "evolution_condition": card.get("evolution_condition", ""),
                        "url": card.get("url", ""),
                        "updated_at": card.get("updated_at", "")
                    }
                    all_cards.append(standardized)
    
    print(f"Total unique cards: {len(all_cards)}")
    
    # Save merged card data
    output_file = DATA_DIR / "cards.json"
    save_json_file(output_file, all_cards)
    
    return all_cards

def process_rulings():
    """Process official QA rulings data"""
    print("\nProcessing rulings...")
    
    # Load official QA CN data
    qa_file = BASE_DIR / "card_game_judge" / "card_game_QA_manger" / "official_qa_cn.json"
    rulings = []
    
    if qa_file.exists():
        print(f"  Loading: {qa_file.name}")
        data = load_json_file(qa_file)
        if data and isinstance(data, list):
            for qa in data:
                # Convert to standard format
                ruling = {
                    "qa_number": qa.get("qa_number", qa.get("id", "")),
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "card_no": qa.get("card_no", ""),
                    "card_name": qa.get("card_name", ""),
                    "product": qa.get("prod_name", ""),
                    "source": qa.get("source", "digimoncard.com"),
                    "url": qa.get("url", ""),
                    "language": qa.get("language", "zh-cn"),
                    "updated_at": qa.get("scraped_at", "")
                }
                rulings.append(ruling)
    
    # Also check finetune origin_data
    origin_qa_file = BASE_DIR / "card_game_judge" / "finetune" / "origin_data" / "official_qa.json"
    if origin_qa_file.exists():
        print(f"  Loading: {origin_qa_file.name}")
        data = load_json_file(origin_qa_file)
        if data and isinstance(data, list):
            for qa in data:
                ruling = {
                    "qa_number": "",
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "card_no": qa.get("card_no", ""),
                    "card_name": qa.get("card_name", ""),
                    "source": qa.get("source", ""),
                    "url": "",
                    "language": "zh-cn",
                    "updated_at": qa.get("date", "")
                }
                # Avoid duplicates
                if not any(r['question'] == ruling['question'] and r['answer'] == ruling['answer'] for r in rulings):
                    rulings.append(ruling)
    
    print(f"Total rulings: {len(rulings)}")
    
    # Save rulings
    output_file = DATA_DIR / "rulings.json"
    save_json_file(output_file, rulings)
    
    return rulings

def extract_rules():
    """Extract rulebook text"""
    print("\nExtracting rules...")
    
    # Try multiple sources
    rule_sources = [
        BASE_DIR / "card_game_judge" / "finetune" / "origin_data" / "rulebook.txt",
        BASE_DIR / "card_game_judge" / "数码宝贝卡牌对战_综合规则_嵌入版.txt",
        BASE_DIR / "card_game_judge" / "数码宝贝卡牌对战_综合规则_新版_完整内容_gemini.txt",
    ]
    
    rules_text = ""
    source_used = None
    
    for source in rule_sources:
        if source.exists():
            print(f"  Loading: {source.name}")
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    rules_text = f.read()
                source_used = source
                break
            except Exception as e:
                print(f"  Error reading {source.name}: {e}")
    
    if not rules_text:
        print("  Warning: No rulebook found!")
        rules_text = "规则书数据未找到"
    else:
        print(f"  Rules loaded from: {source_used.name}")
        print(f"  Rules length: {len(rules_text)} characters")
    
    # Save rules
    output_file = DATA_DIR / "rules.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(rules_text)
    print(f"Saved: {output_file}")
    
    return rules_text

def process_terminology():
    """Process terminology mappings"""
    print("\nProcessing terminology...")
    
    term_mapping_dir = BASE_DIR / "digimon_card_data" / "term_mapping"
    all_terms = {}
    
    # Load all term mapping JSON files
    term_files = list(term_mapping_dir.glob("*.json"))
    
    for term_file in term_files:
        # Skip very large or complex files
        if "llm_config" in term_file.name or "requirements" in term_file.name:
            continue
            
        print(f"  Loading: {term_file.name}")
        data = load_json_file(term_file)
        if data and isinstance(data, dict):
            all_terms.update(data)
    
    # Also check digimon_data directory
    digimon_data_terms = BASE_DIR / "digimon_data" / "dtcg_terminology.json"
    if digimon_data_terms.exists():
        print(f"  Loading: dtcg_terminology.json")
        data = load_json_file(digimon_data_terms)
        if data and isinstance(data, dict):
            all_terms.update(data)
    
    name_mapping = BASE_DIR / "digimon_data" / "digimon_name_mapping_v3.json"
    if name_mapping.exists():
        print(f"  Loading: digimon_name_mapping_v3.json")
        data = load_json_file(name_mapping)
        if data and isinstance(data, dict):
            all_terms["name_mappings"] = data
    
    print(f"Total term entries: {len(all_terms)}")
    
    # Save terminology
    output_file = DATA_DIR / "terms.json"
    save_json_file(output_file, all_terms)
    
    return all_terms

def create_skill_metadata():
    """Create SKILL.md metadata file"""
    print("\nCreating SKILL.md...")
    
    skill_md = """# DTCG Judger Skill - 数码宝贝卡牌裁判技能

## 概述

这是一个用于数码宝贝卡牌对战（Digimon Card Game）的裁判辅助技能。提供卡牌数据查询、规则裁定、术语翻译等功能。

## 功能

### 1. 卡牌查询
- 根据卡牌编号查询卡牌信息
- 根据卡牌名称搜索卡牌
- 支持中文和日文名称检索
- 查看卡牌效果、进化条件、继承效果等

### 2. 规则裁定
- 查询官方 Q&A 裁定
- 根据卡牌或场景检索相关裁定
- 提供规则条文引用

### 3. 规则书
- 完整的游戏综合规则（Ver.3.6）
- 关键词效果解释
- 游戏流程说明

### 4. 术语映射
- 中日术语对照
- 数码兽名称映射
- 游戏机制术语解释

## 数据结构

```
data/
├── cards.json      # 合并后的卡牌数据（去重、标准化）
├── rulings.json    # 官方 Q&A 裁定数据
├── rules.txt       # 综合规则书全文
└── terms.json      # 术语映射表
```

## 使用方法

```python
from src.judger import DTCGJudger

judger = DTCGJudger()

# 查询卡牌
card = judger.search_card("BT24-001")
card = judger.search_card_by_name("基基兽")

# 查询裁定
rulings = judger.search_rulings("安防")
rulings = judger.get_rulings_by_card("BT24-001")

# 查询规则
rules = judger.search_rules("进化")

# 术语翻译
term = judger.translate_term("贯通关")
```

## 数据来源

- 卡牌数据：digimoncard.com 官方数据
- 裁定数据：digimoncard.com 官方 Q&A
- 规则书：数码宝贝卡牌对战 综合规则 Ver.3.6
- 术语映射：社区整理的中日术语对照

## 更新记录

- 2026-03-10: 初始版本，整合卡牌数据、裁定、规则书和术语映射
"""
    
    output_file = SKILL_DIR / "SKILL.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(skill_md)
    print(f"Saved: {output_file}")
    
    return skill_md

def create_judger_code():
    """Create the judger.py source code"""
    print("\nCreating judger.py...")
    
    judger_code = '''#!/usr/bin/env python3
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
        lines = self.rules.split('\\n')
        
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
        lines = self.rules.split('\\n')
        
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
        
        return '\\n'.join(section_content)
    
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
    
    print("\\n=== 数据统计 ===")
    stats = judger.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\\n=== 测试卡牌查询 ===")
    card = judger.search_card("BT24-001")
    if card:
        print(f"找到卡牌：{card.get('card_name')}")
        print(f"效果：{card.get('effect', '无')[:100]}...")
    
    print("\\n=== 测试裁定查询 ===")
    rulings = judger.search_rulings("安防")
    print(f"找到 {len(rulings)} 条相关裁定")
    if rulings:
        print(f"示例：{rulings[0].get('question', '')[:100]}...")
'''
    
    output_file = SKILL_DIR / "src" / "judger.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(judger_code)
    print(f"Saved: {output_file}")
    
    return judger_code


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG Judger Skill Data Processor")
    print("=" * 60)
    
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (SKILL_DIR / "src").mkdir(parents=True, exist_ok=True)
    
    # 处理各类数据
    cards = merge_card_data()
    rulings = process_rulings()
    rules = extract_rules()
    terms = process_terminology()
    
    # 创建技能文档和代码
    create_skill_metadata()
    create_judger_code()
    
    print("\\n" + "=" * 60)
    print("数据处理完成!")
    print("=" * 60)
    print(f"\\n输出目录：{SKILL_DIR}")
    print(f"  - cards.json: {len(cards)} 张卡牌")
    print(f"  - rulings.json: {len(rulings)} 条裁定")
    print(f"  - rules.txt: {len(rules)} 字符")
    print(f"  - terms.json: {len(terms)} 个术语条目")
    print(f"  - SKILL.md: 技能说明文档")
    print(f"  - src/judger.py: 裁判功能代码")


if __name__ == "__main__":
    main()
