#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 terms.json 提取完整的中文→日文数码兽名称映射
并构建别名映射表
"""

import json
import re

def load_terms(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_digimon_name(cn_name):
    """判断是否为数码兽名称"""
    return '兽' in cn_name or '兽' in cn_name or '龙' in cn_name or '天使' in cn_name

def extract_digimon_mappings(terms):
    """从 terms.json 提取数码兽名称映射"""
    cn_to_jp = {}
    jp_to_cn = {}
    
    for cn, jp_list in terms.items():
        if is_digimon_name(cn):
            for jp in jp_list:
                # 只保留纯片假名的日文名
                if re.match(r'^[\u30A0-\u30FF]+$', jp):
                    cn_to_jp[cn] = jp
                    jp_to_cn[jp] = cn
    
    return cn_to_jp, jp_to_cn

def generate_variants(cn_to_jp):
    """基于中文名称生成常见变体"""
    variants = {}
    
    for cn_name in cn_to_jp.keys():
        # 移除"兽"后缀生成简称
        if cn_name.endswith('兽'):
            base = cn_name[:-1]
            variants[base] = cn_name
        elif cn_name.endswith('兽'):
            base = cn_name[:-1]
            variants[base] = cn_name
        
        # 特殊处理：移除"龙"、"天使"等
        for suffix in ['龙兽', '天使兽', '数码兽']:
            if cn_name.endswith(suffix):
                base = cn_name[:-len(suffix)]
                if base:
                    variants[base] = cn_name
        
        # 常见音译变体
        variant_map = {
            '西尔芙': '西尔弗兽',
            '希尔弗': '西尔弗兽',
            '美杜莎': '美杜莎兽',
            '灰姑娘': '灰姑娘兽',
            '靴靴': '靴靴兽',
        }
        for variant, standard in variant_map.items():
            variants[variant] = standard
    
    return variants

def main():
    # 加载 terms.json
    terms = load_terms('skill/data/terms.json')
    print(f"加载了 {len(terms)} 条术语")
    
    # 提取数码兽映射
    cn_to_jp, jp_to_cn = extract_digimon_mappings(terms)
    print(f"找到 {len(cn_to_jp)} 个中文→日文数码兽映射")
    print(f"找到 {len(jp_to_cn)} 个日文→中文数码兽映射")
    
    # 生成变体
    variants = generate_variants(cn_to_jp)
    print(f"生成 {len(variants)} 个变体映射")
    
    # 构建完整的别名映射表
    alias_map = {
        'variants': variants,
        'jp_to_cn': jp_to_cn,
        'suffix_rules': {
            'remove': ['兽', '龙', '天使', '数码兽'],
            'add': ['兽']
        }
    }
    
    # 保存结果
    with open('skill/data/name_aliases.json', 'w', encoding='utf-8') as f:
        json.dump(alias_map, f, ensure_ascii=False, indent=2)
    
    print(f"\n别名映射表已保存到 skill/data/name_aliases.json")
    
    # 输出样本
    print("\n=== 变体映射样本 (前 20 个) ===")
    for i, (variant, standard) in enumerate(list(variants.items())[:20]):
        print(f"  {variant} → {standard}")
    
    print("\n=== 日文→中文映射样本 (前 20 个) ===")
    for i, (jp, cn) in enumerate(list(jp_to_cn.items())[:20]):
        print(f"  {jp} → {cn}")
    
    # 保存详细报告
    with open('skill/data/alias_extraction_report.txt', 'w', encoding='utf-8') as f:
        f.write("别名映射表构建报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"数据源：skill/data/terms.json\n")
        f.write(f"总术语数：{len(terms)}\n")
        f.write(f"数码兽中文→日文映射：{len(cn_to_jp)} 条\n")
        f.write(f"数码兽日文→中文映射：{len(jp_to_cn)} 条\n")
        f.write(f"生成的变体映射：{len(variants)} 条\n\n")
        
        f.write("=== 完整的日文→中文映射 ===\n")
        for jp, cn in sorted(jp_to_cn.items()):
            f.write(f"{jp} → {cn}\n")
        
        f.write("\n=== 完整的变体映射 ===\n")
        for variant, standard in sorted(variants.items()):
            f.write(f"{variant} → {standard}\n")
    
    print(f"\n详细报告已保存到 skill/data/alias_extraction_report.txt")

if __name__ == '__main__':
    main()
