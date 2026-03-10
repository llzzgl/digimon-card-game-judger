#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试卡牌编号提取和标准化功能
"""

from app.query_processor import query_processor
from app.enhanced_query_processor import enhanced_query_processor


def test_card_number_extraction():
    """测试卡牌编号提取"""
    
    test_cases = [
        # (输入, 期望输出)
        ("BT1-001的效果是什么？", ["BT01-001"]),
        ("BT01-001和BT1-002", ["BT01-001", "BT01-002"]),
        ("BT1001能否触发？", ["BT01-001"]),
        ("ST1-01和EX1-001", ["ST01-01", "EX01-001"]),
        ("P-001促销卡", ["P-001"]),
        ("P001和P-002", ["P-001", "P-002"]),
        ("BT-1-001的效果", ["BT01-001"]),
        ("bt01-001小写测试", ["BT01-001"]),
        ("没有卡牌编号的问题", []),
        ("BT20-079和BT20079", ["BT20-079"]),  # 应该去重
    ]
    
    print("=" * 60)
    print("测试基础查询处理器 (query_processor)")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = query_processor.extract_card_numbers(query)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} 输入: {query}")
        print(f"   期望: {expected}")
        print(f"   实际: {result}")
        print()
    
    print(f"结果: {passed} 通过, {failed} 失败")
    print()
    
    # 测试增强版处理器
    print("=" * 60)
    print("测试增强版查询处理器 (enhanced_query_processor)")
    print("=" * 60)
    
    passed2 = 0
    failed2 = 0
    
    for query, expected in test_cases:
        result = enhanced_query_processor.extract_card_numbers(query)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed2 += 1
        else:
            failed2 += 1
        
        print(f"{status} 输入: {query}")
        print(f"   期望: {expected}")
        print(f"   实际: {result}")
        print()
    
    print(f"结果: {passed2} 通过, {failed2} 失败")


def test_query_analysis():
    """测试完整的查询分析"""
    
    print("\n" + "=" * 60)
    print("测试完整查询分析")
    print("=" * 60)
    
    test_queries = [
        "BT01-001登场时效果能否触发？",
        "BT1-002和ST1-01同时触发，哪个先处理？",
        "P-001的反击效果如何使用？",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 60)
        
        # 基础分析
        analysis = query_processor.analyze_query(query)
        print(f"卡牌编号: {analysis['card_numbers']}")
        print(f"内存值: {analysis['memory_values']}")
        print(f"等级: {analysis['levels']}")
        
        # 增强分析
        enhanced = enhanced_query_processor.analyze_scenario(query)
        print(f"问题类型: {enhanced['question_type']}")
        print(f"效果时机: {enhanced['effect_timings']}")
        print(f"需要顺序分析: {enhanced['needs_sequence_analysis']}")
        print(f"搜索查询数: {len(enhanced['search_queries'])}")


if __name__ == "__main__":
    test_card_number_extraction()
    test_query_analysis()
