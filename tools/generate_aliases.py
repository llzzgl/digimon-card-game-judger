#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成别名映射表的辅助脚本
从 cards.json 中提取日文名和中文名，构建映射关系
"""

import json
import re
from collections import defaultdict

def load_cards(filepath):
    """加载卡牌数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_name_parts(name):
    """
    从卡牌名称中提取日文和中文部分
    返回 (日文部分，中文部分)
    """
    # 移除编号前缀
    name_clean = re.sub(r'^[A-Z]+\d+-\d+', '', name).strip()
    
    # 提取片假名
    katakana = re.findall(r'[\u30A0-\u30FF]+', name_clean)
    # 提取中文
    chinese = re.findall(r'[\u4E00-\u9FFF]+', name_clean)
    
    jp_part = ''.join(katakana)
    cn_part = ''.join(chinese)
    
    return jp_part, cn_part, name_clean

def is_digimon_name(name):
    """判断是否为数码兽名称（以モン或兽结尾）"""
    return name.endswith('モン') or name.endswith('兽') or name.endswith('兽')

def generate_variants(name):
    """
    为给定名称生成常见变体
    """
    variants = []
    
    # 移除常见后缀
    for suffix in ['兽', '兽', 'モン', '龙', '天使', '数码兽']:
        if name.endswith(suffix):
            base = name[:-len(suffix)]
            if base:
                variants.append(base)
    
    # 音译变体（常见模式）
    # 这些需要根据实际数据手动补充
    variant_map = {
        '西尔弗兽': ['西尔芙', '希尔弗'],
        '美杜莎兽': ['美杜莎'],
        '灰姑娘兽': ['灰姑娘'],
        '靴靴兽': ['靴靴'],
    }
    
    if name in variant_map:
        variants.extend(variant_map[name])
    
    return variants

def build_alias_mapping(cards):
    """
    构建别名映射表
    """
    variants = {}  # 变体 -> 标准名
    jp_to_cn = {}  # 日文名 -> 中文名
    suffix_rules = {
        'remove': ['兽', '龙', '天使', '数码兽'],
        'add': ['兽']
    }
    
    # 收集所有数码兽名称
    digimon_names = defaultdict(list)
    
    for card in cards:
        name = card.get('card_name', '')
        if not is_digimon_name(name):
            continue
        
        jp_part, cn_part, name_clean = extract_name_parts(name)
        
        # 如果同时有日文和中文部分，建立映射
        if jp_part and cn_part:
            # 提取核心的数码兽名（移除 X 抗体等后缀）
            jp_core = re.sub(r'X 抗体.*$', '', jp_part).strip()
            cn_core = re.sub(r'X 抗体.*$', '', cn_part).strip()
            
            if jp_core and cn_core:
                jp_to_cn[jp_core] = cn_core
        
        # 收集所有名称用于分析
        digimon_names[name_clean].append(card)
    
    # 基于常见模式添加变体
    # 这些需要根据实际数据人工审核
    common_variants = {
        # 简称 -> 全称
        '亚古': '亚古兽',
        '加布': '加布兽',
        '机械暴龙': '机械暴龙兽',
        '战斗暴龙': '战斗暴龙兽',
        '钢铁加鲁鲁': '钢铁加鲁鲁兽',
        '天女': '天女兽',
        '天使': '天使兽',
        '恶魔兽': '恶魔兽',
        '小丑': '小丑皇',
        '吸血': '吸血魔兽',
        '启示录': '启示录兽',
        '光明': '光明兽',
        '混沌': '混沌兽',
        '公爵': '公爵兽',
        '红莲': '红莲骑士兽',
        '阿尔法': '阿尔法兽',
        '奥米加': '奥米加兽',
        '别西卜': '别西卜兽',
        '贝尔菲': '贝尔菲兽',
        '利维坦': '利维坦兽',
        '巴尔': '巴尔兽',
        '莉莉丝': '莉莉丝兽',
        '魔神兽': '魔神兽',
        # 音译变体
        '西尔芙': '西尔弗兽',
        '希尔弗': '西尔弗兽',
        '美杜莎': '美杜莎兽',
        '灰姑娘': '灰姑娘兽',
        '靴靴': '靴靴兽',
    }
    
    variants.update(common_variants)
    
    # 基于日文名添加常见映射
    common_jp_cn = {
        'アグモン': '亚古兽',
        'ガブモン': '加布兽',
        'グレイモン': '古拉兽',
        'ガルルモン': '加鲁鲁兽',
        'エンジェウーモン': '天女兽',
        'デビモン': '恶魔兽',
        'ピエモン': '小丑皇',
        'ヴァンデモン': '吸血魔兽',
        'アポカリモン': '启示录兽',
        'ルチェモン': '光明兽',
        'カオスモン': '混沌兽',
        'デュークモン': '公爵兽',
        'ガルグモン': '红莲骑士兽',
        'アルファモン': '阿尔法兽',
        'オメガモン': '奥米加兽',
        'ベルゼブモン': '别西卜兽',
        'ベルフェモン': '贝尔菲兽',
        'リヴァイアモン': '利维坦兽',
        'バアルモン': '巴尔兽',
        'リリスモン': '莉莉丝兽',
        'デーモン': '魔神兽',
        'シルフィーモン': '西尔弗兽',
        'メデューサモン': '美杜莎兽',
        'シンデレラモン': '灰姑娘兽',
        'シューシューモン': '靴靴兽',
    }
    
    jp_to_cn.update(common_jp_cn)
    
    return {
        'variants': variants,
        'jp_to_cn': jp_to_cn,
        'suffix_rules': suffix_rules
    }

def main():
    # 加载数据
    cards = load_cards('skill/data/cards.json')
    print(f"加载了 {len(cards)} 张卡牌")
    
    # 构建映射表
    alias_map = build_alias_mapping(cards)
    
    # 保存结果
    with open('skill/data/name_aliases.json', 'w', encoding='utf-8') as f:
        json.dump(alias_map, f, ensure_ascii=False, indent=2)
    
    print(f"\n别名映射表已保存到 skill/data/name_aliases.json")
    print(f"变体映射：{len(alias_map['variants'])} 条")
    print(f"日文→中文映射：{len(alias_map['jp_to_cn'])} 条")
    
    # 输出样本
    print("\n=== 变体映射样本 ===")
    for i, (variant, standard) in enumerate(list(alias_map['variants'].items())[:10]):
        print(f"  {variant} → {standard}")
    
    print("\n=== 日文→中文映射样本 ===")
    for i, (jp, cn) in enumerate(list(alias_map['jp_to_cn'].items())[:10]):
        print(f"  {jp} → {cn}")

if __name__ == '__main__':
    main()
