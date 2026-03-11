#!/usr/bin/env python3
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 检查卡牌名称格式
cards = json.load(open('skill/data/cards.json', 'r', encoding='utf-8'))

# 查找亚古兽相关的卡牌
agumon_cards = [c for c in cards if 'アグモン' in c.get('card_name', '') or '亚古兽' in c.get('card_name', '')]

print(f"找到 {len(agumon_cards)} 张亚古兽相关卡牌")
print("\n样本:")
for card in agumon_cards[:10]:
    print(f"  {card.get('card_no')}: {card.get('card_name')}")

# 检查名称索引的关键词
import re

def extract_keywords(text, max_keywords=50):
    keywords = []
    text = text.strip()
    text_len = len(text)
    max_text_len = 100
    if text_len > max_text_len:
        text = text[:max_text_len]
        text_len = max_text_len
    
    for i in range(text_len):
        for length in [2, 3]:
            if i + length <= text_len:
                kw = text[i:i+length]
                if kw and not kw.isdigit() and not re.match(r'^[^\u4e00-\u9fa5a-zA-Z]+$', kw):
                    keywords.append(kw)
        if len(keywords) >= max_keywords:
            break
    
    return keywords[:max_keywords]

# 检查"亚古兽"是否在索引中
test_name = "BT24-001 亚古兽"
keywords = extract_keywords(test_name.lower())
print(f"\n'{test_name}' 提取的关键词：{keywords[:20]}")
print(f"'亚古' 是否在关键词中：{'亚古' in keywords}")
print(f"'亚古兽' 是否在关键词中：{'亚古兽' in keywords}")
