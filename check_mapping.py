#!/usr/bin/env python3
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

aliases = json.load(open('skill/data/name_aliases.json', 'r', encoding='utf-8'))

print("=== 检查亚古兽相关映射 ===")
print(f"variants 中有 '亚古': {'亚古' in aliases['variants']}")
if '亚古' in aliases['variants']:
    print(f"  '亚古' → '{aliases['variants']['亚古']}'")

print(f"\njp_to_cn 中有 'アグモン': {'アグモン' in aliases['jp_to_cn']}")
if 'アグモン' in aliases['jp_to_cn']:
    print(f"  'アグモン' → '{aliases['jp_to_cn']['アグモン']}'")

# 构建反向映射
cn_to_jp = {v: k for k, v in aliases['jp_to_cn'].items()}
print(f"\ncn_to_jp 中有 '亚古兽': {'亚古兽' in cn_to_jp}")
if '亚古兽' in cn_to_jp:
    print(f"  '亚古兽' → '{cn_to_jp['亚古兽']}'")

# 检查卡牌数据中的名称
cards = json.load(open('skill/data/cards.json', 'r', encoding='utf-8'))
agumon_cards = [c for c in cards if 'アグモン' in c.get('card_name', '')][:5]
print(f"\n卡牌数据中的亚古兽样本:")
for card in agumon_cards:
    print(f"  {card.get('card_no')}: {card.get('card_name')}")
