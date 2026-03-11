#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 cards.json 中的卡牌名称模式"""

import json
import re
import sys
from collections import Counter

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

# 加载数据
with open('skill/data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

output_lines = []
output_lines.append(f"总卡牌数：{len(cards)}")

# 提取所有唯一名称
names = set()
for card in cards:
    name = card.get('card_name', '')
    if name:
        # 移除编号前缀
        name_clean = re.sub(r'^[A-Z]+\d+-\d+', '', name).strip()
        names.add(name_clean)

output_lines.append(f"唯一名称数：{len(names)}")

# 分析名称模式
jp_names = []
cn_names = []
mixed_names = []

for name in names:
    katakana = re.findall(r'[\u30A0-\u30FF]+', name)
    kanji_cn = re.findall(r'[\u4E00-\u9FFF]+', name)
    
    if katakana and not kanji_cn:
        jp_names.append(name)
    elif kanji_cn and not katakana:
        cn_names.append(name)
    else:
        mixed_names.append(name)

output_lines.append(f"\n纯日文名：{len(jp_names)}")
output_lines.append(f"纯中文名：{len(cn_names)}")
output_lines.append(f"混合名：{len(mixed_names)}")

output_lines.append("\n=== 纯日文名样本 (50 个) ===")
for name in jp_names[:50]:
    output_lines.append(name)

output_lines.append("\n=== 纯中文名样本 (50 个) ===")
for name in cn_names[:50]:
    output_lines.append(name)

output_lines.append("\n=== 混合名样本 (50 个) ===")
for name in mixed_names[:50]:
    output_lines.append(name)

# 分析常见后缀
suffixes = Counter()
for name in names:
    if name.endswith('モン'):
        suffixes['モン'] += 1
    if name.endswith('兽'):
        suffixes['兽'] += 1
    if name.endswith('龙'):
        suffixes['龙'] += 1
    if name.endswith('天使'):
        suffixes['天使'] += 1

output_lines.append("\n=== 常见后缀统计 ===")
for suffix, count in suffixes.most_common(10):
    output_lines.append(f"{suffix}: {count}")

# 提取日文名到中文名的映射（从混合名中）
jp_to_cn_candidates = []
for name in mixed_names:
    katakana = ''.join(re.findall(r'[\u30A0-\u30FF]+', name))
    cn_part = ''.join(re.findall(r'[\u4E00-\u9FFF]+', name))
    if katakana and cn_part:
        jp_to_cn_candidates.append((katakana, cn_part, name))

output_lines.append(f"\n=== 日文→中文映射候选 ({len(jp_to_cn_candidates)} 个) ===")
for jp, cn, full in jp_to_cn_candidates[:100]:
    output_lines.append(f"{jp} → {cn} (完整：{full})")

# 保存分析结果
with open('skill/data/name_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("分析完成！结果已保存到 skill/data/name_analysis.txt")
print(f"总卡牌数：{len(cards)}")
print(f"唯一名称数：{len(names)}")
print(f"纯日文名：{len(jp_names)}")
print(f"纯中文名：{len(cn_names)}")
print(f"混合名：{len(mixed_names)}")
print(f"日文→中文映射候选：{len(jp_to_cn_candidates)}")
