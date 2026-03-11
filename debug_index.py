#!/usr/bin/env python3
import sys
sys.path.insert(0, 'D:\\LLMProject\\dtcg_judger')
sys.stdout.reconfigure(encoding='utf-8')

from skill.src.judger import DTCGJudger

judger = DTCGJudger()

print("=== 检查索引结构 ===\n")

# 检查"アグ"关键词
kw = 'アグ'
print(f"关键词 '{kw}' 在索引中：{kw in judger.card_name_index}")
if kw in judger.card_name_index:
    cards = judger.card_name_index[kw]
    print(f"  卡牌数量：{len(cards)}")
    if cards:
        print(f"  第一张卡牌：{cards[0].get('card_name')}")
else:
    print(f"  索引中所有包含'{kw}'的关键词:")
    for k in judger.card_name_index.keys():
        if kw in k:
            print(f"    {k}: {len(judger.card_name_index[k])} 张")

# 直接搜索卡牌名称
print(f"\n=== 直接搜索卡牌 ===")
for card in judger.cards[:20]:
    name = card.get('card_name', '')
    if 'アグモン' in name:
        print(f"  {card.get('card_no')}: {name}")
        keywords = judger._extract_keywords(name.lower())
        print(f"    关键词：{keywords[:10]}")
