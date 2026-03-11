#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTCG Judger 性能对比测试 - 优化前后对比
"""

import time
import tracemalloc
import sys
import json
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "skill" / "src"))

from judger import DTCGJudger


def benchmark_initialization():
    """基准测试：初始化耗时"""
    print("=" * 70)
    print("基准测试 1: 初始化耗时（含数据加载和索引构建）")
    print("=" * 70)
    
    tracemalloc.start()
    start = time.perf_counter()
    judger = DTCGJudger()
    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    init_time_ms = elapsed * 1000
    peak_memory_mb = peak / 1024 / 1024
    
    print(f"\n[OK] 初始化耗时：{init_time_ms:.2f} ms ({init_time_ms/1000:.2f} s)")
    print(f"[OK] 峰值内存：{peak_memory_mb:.2f} MB")
    print(f"[OK] 卡牌数量：{len(judger.cards)}")
    print(f"[OK] 裁定数量：{len(judger.rulings)}")
    print(f"[OK] 卡牌编号索引：{len(judger.card_no_index)} 条目")
    print(f"[OK] 卡牌名称索引：{len(judger.card_name_index)} 关键词")
    print(f"[OK] 裁定索引：{len(judger.ruling_index)} 关键词")
    
    return {
        'init_time_ms': init_time_ms,
        'peak_memory_mb': peak_memory_mb,
        'judger': judger
    }


def benchmark_queries(judger, iterations=20):
    """基准测试：查询性能"""
    print("\n" + "=" * 70)
    print(f"基准测试 2: 查询性能（平均 {iterations} 次）")
    print("=" * 70)
    
    test_cases = [
        ("search_card (编号查询)", "search_card", "BT24-001"),
        ("search_card (EX 系列)", "search_card", "EX8-001"),
        ("search_card_by_name (亚古兽)", "search_card_by_name", "亚古兽"),
        ("search_card_by_name (奥米加)", "search_card_by_name", "奥米加"),
        ("search_rulings (进化)", "search_rulings", "进化"),
        ("search_rulings (安防)", "search_rulings", "安防"),
        ("translate_term (进化源)", "translate_term", "进化源"),
        ("translate_term (数码宝贝)", "translate_term", "数码宝贝"),
    ]
    
    results = {}
    
    for name, method_name, query in test_cases:
        method = getattr(judger, method_name)
        
        tracemalloc.start()
        times = []
        
        for i in range(iterations):
            start = time.perf_counter()
            result = method(query)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # 计算结果数量
        if isinstance(result, list):
            result_count = len(result)
        elif result is None:
            result_count = 0
        else:
            result_count = 1
        
        results[method_name] = {
            'query': query,
            'avg_ms': avg_time,
            'min_ms': min_time,
            'max_ms': max_time,
            'result_count': result_count
        }
        
        print(f"\n{name}('{query}'):")
        print(f"  平均：{avg_time:.3f} ms | 最小：{min_time:.3f} ms | 最大：{max_time:.3f} ms")
        print(f"  结果数：{result_count}")
    
    return results


def benchmark_memory_efficiency(judger):
    """基准测试：内存效率分析"""
    print("\n" + "=" * 70)
    print("基准测试 3: 内存效率分析")
    print("=" * 70)
    
    # 估算索引内存占用
    import sys
    
    card_no_index_size = sys.getsizeof(judger.card_no_index)
    card_name_index_size = sys.getsizeof(judger.card_name_index)
    ruling_index_size = sys.getsizeof(judger.ruling_index)
    
    print(f"\n索引数据结构大小估算:")
    print(f"  卡牌编号索引：{card_no_index_size / 1024:.2f} KB")
    print(f"  卡牌名称索引：{card_name_index_size / 1024:.2f} KB")
    print(f"  裁定索引：{ruling_index_size / 1024:.2f} KB")
    
    # 计算平均查询速度
    print(f"\n查询速度评级:")
    print(f"  卡牌编号查询：O(1) - 优秀 (A+)")
    print(f"  卡牌名称查询：O(1)~O(k) - 良好 (A) (k 为关键词匹配数)")
    print(f"  裁定查询：O(1)~O(k) - 良好 (A)")
    print(f"  术语翻译：O(n) - 待优化 (C)")


def generate_report(init_result, query_results, memory_result):
    """生成性能报告"""
    print("\n" + "=" * 70)
    print("性能测试总结报告")
    print("=" * 70)
    
    init_time = init_result['init_time_ms']
    peak_memory = init_result['peak_memory_mb']
    
    # 评级标准
    if init_time < 5000:
        init_rating = "优秀 (A+)"
    elif init_time < 10000:
        init_rating = "良好 (A)"
    elif init_time < 20000:
        init_rating = "中等 (B)"
    else:
        init_rating = "待优化 (C)"
    
    print(f"\n【初始化性能】")
    print(f"  耗时：{init_time:.2f} ms ({init_time/1000:.2f} s)")
    print(f"  评级：{init_rating}")
    
    print(f"\n【内存效率】")
    print(f"  峰值内存：{peak_memory:.2f} MB")
    print(f"  数据规模：{len(init_result['judger'].cards)} 卡牌 + {len(init_result['judger'].rulings)} 裁定")
    
    print(f"\n【查询性能】")
    for method_name, result in query_results.items():
        avg = result['avg_ms']
        if avg < 1:
            rating = "优秀 (A+)"
        elif avg < 10:
            rating = "良好 (A)"
        elif avg < 50:
            rating = "中等 (B)"
        else:
            rating = "待优化 (C)"
        print(f"  {method_name}: {avg:.3f} ms - {rating}")
    
    print(f"\n【优化建议】")
    if init_time > 10000:
        print(f"  [WARN] 初始化时间较长，建议:")
        print(f"    - 使用 pickle 预构建索引文件")
        print(f"    - 异步加载非关键数据")
        print(f"    - 延迟加载大型数据（规则书）")
    
    # 术语翻译优化建议
    if 'translate_term' in query_results:
        term_time = query_results['translate_term']['avg_ms']
        if term_time > 1:
            print(f"  [WARN] 术语翻译性能可优化:")
            print(f"    - 构建双向术语索引（cn->jp, jp->cn）")
            print(f"    - 使用字典替代线性搜索")
    
    return {
        'init_time_ms': init_time,
        'peak_memory_mb': peak_memory,
        'query_results': query_results,
        'rating': init_rating
    }


def main():
    """运行所有基准测试"""
    print("\n" + "=" * 70)
    print("DTCG Judger 性能基准测试 - 优化版")
    print("=" * 70 + "\n")
    
    # 测试 1: 初始化
    init_result = benchmark_initialization()
    
    # 测试 2: 查询性能
    query_results = benchmark_queries(init_result['judger'])
    
    # 测试 3: 内存效率
    benchmark_memory_efficiency(init_result['judger'])
    
    # 生成报告
    report = generate_report(init_result, query_results, init_result)
    
    # 保存结果到 JSON
    output_file = Path(__file__).parent / "perf_results_optimized.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'init_time_ms': report['init_time_ms'],
            'peak_memory_mb': report['peak_memory_mb'],
            'query_results': {k: {'avg_ms': v['avg_ms'], 'result_count': v['result_count']} 
                            for k, v in report['query_results'].items()},
            'rating': report['rating']
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 测试结果已保存到：{output_file}")
    
    return report


if __name__ == "__main__":
    report = main()
