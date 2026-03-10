#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查卡牌数据"""
import json
import sys

# 检查卡牌数据文件
card_file = "../digimon_card_data/digimon_card_data_chiness/digimon_cards_cn.json"

try:
    with open(card_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 成功加载卡牌数据")
    print(f"   总卡牌数: {len(data)}")
    
    # 检查第一张卡
    if data:
        first_card = data[0]
        print(f"\n示例卡牌:")
        print(f"   编号: {first_card.get('card_no', 'N/A')}")
        print(f"   名称: {first_card.get('name_cn', 'N/A')}")
        print(f"   字段: {list(first_card.keys())}")
    
    # 检查BT23卡牌
    bt23_cards = [c for c in data if c.get('card_no', '').startswith('BT23')]
    print(f"\nBT23系列卡牌数: {len(bt23_cards)}")
    
    # 检查特定卡牌
    test_cards = ['BT23-032', 'BT24-016', 'BT23-027', 'BT23-050', 'BT21-001']
    print(f"\n检查特定卡牌:")
    for card_no in test_cards:
        found = any(c.get('card_no') == card_no for c in data)
        status = "✅" if found else "❌"
        print(f"   {status} {card_no}")
    
    # 检查编号格式
    print(f"\n编号格式示例:")
    for card in data[:5]:
        print(f"   {card.get('card_no', 'N/A')}")
    
except FileNotFoundError:
    print(f"❌ 文件不存在: {card_file}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ JSON解析失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
