#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 cards.json 中提取更完整的日文→中文映射
通过分析同时包含日文和中文的卡牌名称
"""

import json
import re
from collections import defaultdict

def load_cards(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_katakana(text):
    """提取片假名"""
    return ''.join(re.findall(r'[\u30A0-\u30FF]+', text))

def extract_chinese(text):
    """提取中文"""
    return ''.join(re.findall(r'[\u4E00-\u9FFF]+', text))

def clean_name(name):
    """清理名称，移除编号前缀和常见后缀"""
    # 移除编号前缀
    name = re.sub(r'^[A-Z]+\d+-\d+', '', name).strip()
    # 移除 X 抗体等后缀
    name = re.sub(r'X 抗体.*$', '', name)
    name = re.sub(r'ACE.*$', '', name)
    name = re.sub(r' -.*$', '', name)
    return name.strip()

def main():
    cards = load_cards('skill/data/cards.json')
    print(f"加载了 {len(cards)} 张卡牌")
    
    # 收集所有包含日文和中文的名称
    jp_cn_pairs = defaultdict(set)
    
    for card in cards:
        name = card.get('card_name', '')
        cleaned = clean_name(name)
        
        # 提取日文和中文部分
        katakana = extract_katakana(cleaned)
        chinese = extract_chinese(cleaned)
        
        # 如果是数码兽名称（以モン结尾的日文）
        if katakana.endswith('モン') and chinese:
            # 尝试提取核心的数码兽名
            jp_core = katakana
            cn_core = chinese
            
            # 如果中文部分包含"兽"，尝试提取
            if '兽' in cn_core or '兽' in cn_core:
                jp_cn_pairs[jp_core].add(cn_core)
    
    # 输出统计
    print(f"\n找到 {len(jp_cn_pairs)} 个日文→中文映射候选")
    
    # 保存候选映射供人工审核
    candidates = {}
    for jp, cn_set in jp_cn_pairs.items():
        cn_list = list(cn_set)
        if len(cn_list) == 1:
            candidates[jp] = cn_list[0]
        else:
            candidates[jp] = cn_list
    
    # 保存结果
    with open('skill/data/jp_cn_candidates.json', 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    
    print(f"候选映射已保存到 skill/data/jp_cn_candidates.json")
    
    # 输出样本
    print("\n=== 映射样本 (前 50 个) ===")
    for i, (jp, cn) in enumerate(list(candidates.items())[:50]):
        if isinstance(cn, list):
            print(f"  {jp} → {cn}")
        else:
            print(f"  {jp} → {cn}")

if __name__ == '__main__':
    main()
