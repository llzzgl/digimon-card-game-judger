#!/usr/bin/env python3
import json
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

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
                # 允许中文、日文、拉丁字母
                if kw and not kw.isdigit() and not re.match(r'^[^\u4e00-\u9fa5\u30A0-\u30FF\u3040-\u309Fa-zA-Z]+$', kw):
                    keywords.append(kw)
        if len(keywords) >= max_keywords:
            break
    
    return keywords[:max_keywords]

# 检查索引中是否有"アグ"或"グモ"等关键词
cards = json.load(open('skill/data/cards.json', 'r', encoding='utf-8'))

# 构建关键词索引测试
card_name_index = {}
for card in cards[:1000]:  # 只测试前 1000 张
    name = card.get('card_name', '').lower()
    if name:
        keywords = extract_keywords(name)
        for kw in keywords:
            if kw not in card_name_index:
                card_name_index[kw] = []
            card_name_index[kw].append(card)

print(f"索引中的关键词数：{len(card_name_index)}")
print(f"\n'アグ' 在索引中：{'アグ' in card_name_index}")
print(f"'グモン' 在索引中：{'グモン' in card_name_index}")
print(f"'アグモン' 在索引中：{'アグモン' in card_name_index}")
print(f"'agum' 在索引中：{'agum' in card_name_index}")

# 检查"亚古"相关
print(f"\n'亚古' 在索引中：{'亚古' in card_name_index}")
print(f"'亚古兽' 在索引中：{'亚古兽' in card_name_index}")

# 显示包含"アグ"的关键词
print(f"\n包含'アグ'的关键词:")
for kw in card_name_index.keys():
    if 'アグ' in kw:
        print(f"  {kw}: {len(card_name_index[kw])} 张卡牌")
        if len(card_name_index[kw]) <= 3:
            for card in card_name_index[kw]:
                print(f"    - {card.get('card_name')}")
