#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger 性能基准测试
对比索引优化前后的查询性能
"""

import time
import random
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from judger import DTCGJudger


def benchmark_card_no_search(judger: DTCGJudger, iterations: int = 1000):
    """测试卡牌编号查询性能"""
    print(f"\n=== 卡牌编号查询测试 ({iterations} 次) ===")
    
    # 获取一些真实的卡牌编号用于测试
    test_card_nos = []
    for card in judger.cards[:min(100, len(judger.cards))]:
        card_no = card.get('card_no', '')
        if card_no:
            test_card_nos.append(card_no)
    
    if not test_card_nos:
        print("[WARN] 没有可用的卡牌编号进行测试")
        return 0, 0
    
    # 测试索引查询
    start = time.perf_counter()
    for _ in range(iterations):
        card_no = random.choice(test_card_nos)
        result = judger.search_card(card_no)
    indexed_time = time.perf_counter() - start
    
    print(f"[OK] 索引查询耗时：{indexed_time:.4f}s")
    print(f"[OK] 平均每次查询：{indexed_time/iterations*1000000:.2f}us")
    
    # 模拟线性查询（用于对比）
    start = time.perf_counter()
    for _ in range(iterations):
        card_no = random.choice(test_card_nos)
        card_no = card_no.strip().upper()
        import re
        card_no = re.sub(r'^(EX)0(\d-)', r'\1\2', card_no)
        card_no = re.sub(r'^(BT)0(\d-)', r'\1\2', card_no)
        # 线性搜索
        for card in judger.cards:
            if card.get('card_no', '').upper() == card_no:
                break
    linear_time = time.perf_counter() - start
    
    print(f"[SL] 线性查询耗时：{linear_time:.4f}s")
    print(f"[SL] 平均每次查询：{linear_time/iterations*1000000:.2f}us")
    
    speedup = linear_time / indexed_time if indexed_time > 0 else float('inf')
    print(f"\n[SPEEDUP] 性能提升：{speedup:.1f}x")
    
    return indexed_time, linear_time


def benchmark_card_name_search(judger: DTCGJudger, iterations: int = 100):
    """测试卡牌名称搜索性能"""
    print(f"\n=== 卡牌名称搜索测试 ({iterations} 次) ===")
    
    # 获取一些真实的卡牌名称用于测试
    test_names = []
    for card in judger.cards[:min(50, len(judger.cards))]:
        name = card.get('card_name', '')
        if name and len(name) > 2:
            test_names.append(name[:min(4, len(name))])  # 使用前 2-4 个字
    
    if not test_names:
        print("[WARN] 没有可用的卡牌名称进行测试")
        return 0, 0
    
    # 测试索引查询
    start = time.perf_counter()
    for _ in range(iterations):
        name = random.choice(test_names)
        result = judger.search_card_by_name(name)
    indexed_time = time.perf_counter() - start
    
    print(f"[OK] 索引查询耗时：{indexed_time:.4f}s")
    print(f"[OK] 平均每次查询：{indexed_time/iterations*1000:.2f}ms")
    
    # 模拟线性查询
    start = time.perf_counter()
    for _ in range(iterations):
        name = random.choice(test_names)
        name = name.strip().lower()
        results = []
        for card in judger.cards:
            card_name = card.get('card_name', '').lower()
            if name in card_name:
                results.append(card)
    linear_time = time.perf_counter() - start
    
    print(f"[SL] 线性查询耗时：{linear_time:.4f}s")
    print(f"[SL] 平均每次查询：{linear_time/iterations*1000:.2f}ms")
    
    speedup = linear_time / indexed_time if indexed_time > 0 else float('inf')
    print(f"\n[SPEEDUP] 性能提升：{speedup:.1f}x")
    
    return indexed_time, linear_time


def benchmark_ruling_search(judger: DTCGJudger, iterations: int = 100):
    """测试 QA 裁定搜索性能"""
    print(f"\n=== QA 裁定搜索测试 ({iterations} 次) ===")
    
    # 获取一些真实的关键词用于测试
    test_keywords = ['进化', '登场', '攻击', '手牌', '安防']
    
    if not judger.rulings:
        print("[WARN] 没有裁定数据可用")
        return 0, 0
    
    # 测试索引查询
    start = time.perf_counter()
    for _ in range(iterations):
        keyword = random.choice(test_keywords)
        result = judger.search_rulings(keyword)
    indexed_time = time.perf_counter() - start
    
    print(f"[OK] 索引查询耗时：{indexed_time:.4f}s")
    print(f"[OK] 平均每次查询：{indexed_time/iterations*1000:.2f}ms")
    
    # 模拟线性查询
    start = time.perf_counter()
    for _ in range(iterations):
        keyword = random.choice(test_keywords)
        keyword = keyword.lower()
        results = []
        for ruling in judger.rulings:
            question = ruling.get('question', '').lower()
            answer = ruling.get('answer', '').lower()
            if keyword in question or keyword in answer:
                results.append(ruling)
    linear_time = time.perf_counter() - start
    
    print(f"[SL] 线性查询耗时：{linear_time:.4f}s")
    print(f"[SL] 平均每次查询：{linear_time/iterations*1000:.2f}ms")
    
    speedup = linear_time / indexed_time if indexed_time > 0 else float('inf')
    print(f"\n[SPEEDUP] 性能提升：{speedup:.1f}x")
    
    return indexed_time, linear_time


def benchmark_index_build_time(judger: DTCGJudger):
    """测试索引构建时间（已在初始化时完成）"""
    print(f"\n=== 索引构建时间 ===")
    print("索引在 DTCGJudger 初始化时自动构建")
    print(f"卡牌编号索引：{len(judger.card_no_index)} 条目")
    print(f"卡牌名称索引：{len(judger.card_name_index)} 关键词")
    print(f"QA 裁定索引：{len(judger.ruling_index)} 关键词")
    print(f"规则章节索引：{len(judger.rule_section_index)} 章节")


def main():
    print("=" * 60)
    print("DTCG Judger 性能基准测试")
    print("=" * 60)
    
    # 初始化裁判器（会自动构建索引）
    print("\n正在初始化 DTCGJudger...")
    start = time.perf_counter()
    judger = DTCGJudger()
    init_time = time.perf_counter() - start
    print(f"初始化完成，耗时：{init_time:.2f}s")
    
    # 显示数据统计
    stats = judger.get_stats()
    print(f"\n数据规模:")
    print(f"  卡牌数量：{stats['total_cards']}")
    print(f"  裁定数量：{stats['total_rulings']}")
    print(f"  规则长度：{stats['rules_length']} 字符")
    
    # 显示索引统计
    index_stats = judger.get_index_stats()
    print(f"\n索引规模:")
    print(f"  卡牌编号索引：{index_stats['card_no_index_entries']} 条目")
    print(f"  卡牌名称索引：{index_stats['card_name_index_keywords']} 关键词")
    print(f"  QA 裁定索引：{index_stats['ruling_index_keywords']} 关键词")
    print(f"  规则章节索引：{index_stats['rule_section_index_sections']} 章节")
    print(f"  估算内存占用：{index_stats['index_memory_estimate_bytes'] / 1024:.2f} KB")
    
    # 运行基准测试
    benchmark_index_build_time(judger)
    
    card_no_indexed, card_no_linear = benchmark_card_no_search(judger)
    card_name_indexed, card_name_linear = benchmark_card_name_search(judger)
    ruling_indexed, ruling_linear = benchmark_ruling_search(judger)
    
    # 总结
    print("\n" + "=" * 60)
    print("性能测试总结")
    print("=" * 60)
    
    total_indexed = card_no_indexed + card_name_indexed + ruling_indexed
    total_linear = card_no_linear + card_name_linear + ruling_linear
    
    if total_indexed > 0:
        overall_speedup = total_linear / total_indexed
        print(f"总体性能提升：{overall_speedup:.1f}x")
        print(f"索引查询总耗时：{total_indexed:.4f}s")
        print(f"线性查询总耗时：{total_linear:.4f}s")
        print(f"节省时间：{total_linear - total_indexed:.4f}s ({(1 - total_indexed/total_linear)*100:.1f}%)")
    
    print("\n[OK] 性能测试完成")


if __name__ == "__main__":
    main()
