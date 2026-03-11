#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger 性能测试脚本
测量初始化、查询耗时和内存占用
"""

import time
import tracemalloc
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "skill" / "src"))

from judger import DTCGJudger


def test_initialization_time():
    """测试初始化耗时（包含数据加载）"""
    print("=" * 60)
    print("测试 1: 初始化耗时")
    print("=" * 60)
    
    tracemalloc.start()
    
    start_time = time.perf_counter()
    judger = DTCGJudger()
    end_time = time.perf_counter()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    init_time_ms = (end_time - start_time) * 1000
    peak_memory_mb = peak / 1024 / 1024
    
    print(f"初始化耗时：{init_time_ms:.2f} ms")
    print(f"峰值内存占用：{peak_memory_mb:.2f} MB")
    print(f"当前内存占用：{current / 1024 / 1024:.2f} MB")
    
    return init_time_ms, peak_memory_mb, judger


def test_first_query(judger):
    """测试首次查询耗时"""
    print("\n" + "=" * 60)
    print("测试 2: 首次查询耗时")
    print("=" * 60)
    
    test_cases = [
        ("search_card", "BT24-001"),
        ("search_card_by_name", "亚古兽"),
        ("search_rulings", "进化"),
        ("translate_term", "进化源"),
    ]
    
    results = {}
    
    for method_name, query in test_cases:
        method = getattr(judger, method_name)
        
        tracemalloc.start()
        start_time = time.perf_counter()
        result = method(query)
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        query_time_ms = (end_time - start_time) * 1000
        memory_mb = peak / 1024 / 1024
        
        if isinstance(result, list):
            result_count = len(result)
        elif result is None:
            result_count = 0
        else:
            result_count = 1
        
        results[method_name] = {
            "time_ms": query_time_ms,
            "memory_mb": memory_mb,
            "result_count": result_count
        }
        
        print(f"{method_name}('{query}'):")
        print(f"  耗时：{query_time_ms:.2f} ms")
        print(f"  内存：{memory_mb:.2f} MB")
        print(f"  结果数：{result_count}")
    
    return results


def test_subsequent_queries(judger, iterations=10):
    """测试后续查询耗时（多次查询取平均）"""
    print("\n" + "=" * 60)
    print(f"测试 3: 后续查询耗时 (平均 {iterations} 次)")
    print("=" * 60)
    
    test_cases = [
        ("search_card", "BT24-001"),
        ("search_card_by_name", "亚古兽"),
        ("search_rulings", "进化"),
        ("translate_term", "进化源"),
    ]
    
    results = {}
    
    for method_name, query in test_cases:
        method = getattr(judger, method_name)
        
        times = []
        tracemalloc.start()
        
        for i in range(iterations):
            start_time = time.perf_counter()
            result = method(query)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        avg_time_ms = sum(times) / len(times)
        min_time_ms = min(times)
        max_time_ms = max(times)
        memory_mb = peak / 1024 / 1024
        
        results[method_name] = {
            "avg_time_ms": avg_time_ms,
            "min_time_ms": min_time_ms,
            "max_time_ms": max_time_ms,
            "memory_mb": memory_mb
        }
        
        print(f"{method_name}('{query}'):")
        print(f"  平均耗时：{avg_time_ms:.2f} ms")
        print(f"  最小耗时：{min_time_ms:.2f} ms")
        print(f"  最大耗时：{max_time_ms:.2f} ms")
        print(f"  内存：{memory_mb:.2f} MB")
    
    return results


def analyze_search_performance(judger):
    """分析搜索算法性能瓶颈"""
    print("\n" + "=" * 60)
    print("测试 4: 搜索算法性能分析")
    print("=" * 60)
    
    # 分析 search_card 的线性搜索
    print("\nsearch_card 性能分析:")
    print(f"  卡牌总数：{len(judger.cards)}")
    print(f"  当前算法：线性搜索 O(n)")
    print(f"  最坏情况：需要遍历所有 {len(judger.cards)} 张卡牌")
    
    # 分析 search_card_by_name 的线性搜索
    print("\nsearch_card_by_name 性能分析:")
    print(f"  卡牌总数：{len(judger.cards)}")
    print(f"  当前算法：线性搜索 O(n)")
    print(f"  每次查询需要遍历所有卡牌")
    
    # 分析 search_rulings 的线性搜索
    print("\nsearch_rulings 性能分析:")
    print(f"  裁定总数：{len(judger.rulings)}")
    print(f"  当前算法：线性搜索 O(n)")
    print(f"  每次查询需要遍历所有裁定")
    
    # 分析 translate_term 的线性搜索
    print("\ntranslate_term 性能分析:")
    print(f"  术语总数：{len(judger.terms)}")
    print(f"  当前算法：线性搜索 O(n)")
    print(f"  每次查询需要遍历所有术语")


def main():
    """运行所有性能测试"""
    print("DTCG Judger 性能测试")
    print("=" * 60)
    
    # 测试 1: 初始化
    init_time, peak_memory, judger = test_initialization_time()
    
    # 测试 2: 首次查询
    first_query_results = test_first_query(judger)
    
    # 测试 3: 后续查询
    subsequent_results = test_subsequent_queries(judger)
    
    # 测试 4: 性能分析
    analyze_search_performance(judger)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("性能测试汇总")
    print("=" * 60)
    print(f"初始化耗时：{init_time:.2f} ms")
    print(f"峰值内存：{peak_memory:.2f} MB")
    print(f"卡牌数量：{len(judger.cards)}")
    print(f"裁定数量：{len(judger.rulings)}")
    print(f"术语数量：{len(judger.terms)}")
    
    return {
        "init_time_ms": init_time,
        "peak_memory_mb": peak_memory,
        "first_query": first_query_results,
        "subsequent_queries": subsequent_results,
        "stats": judger.get_stats()
    }


if __name__ == "__main__":
    results = main()
