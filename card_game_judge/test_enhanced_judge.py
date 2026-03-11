# -*- coding: utf-8 -*-
"""
测试增强版裁判系统
对比改进前后的效果
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# 测试用例
TEST_CASES = [
    {
        "name": "复杂场面分析 - 土偶兽联展",
        "question": """我方联展了 bt23-032 土偶兽，把对方的数码兽退化成 bt24-016 拉米亚兽，并选择其主要阶段开始时攻击。
土偶进化源中有 bt23-027 天使兽和 bt23-050 甲龙兽。
对方拉米亚进化源中有 bt21-001 基基兽。
此时移交回合后会发生什么？""",
        "expected_features": ["sequence", "timing", "card"]
    },
    {
        "name": "效果处理顺序 - 同时触发",
        "question": """我的数码兽攻击对手，对战中消灭了对手的数码兽。
我的数码兽有≪贯通≫效果，同时有【消灭对手数码兽时】的效果。
请问这两个效果如何处理？""",
        "expected_features": ["sequence", "timing"]
    },
    {
        "name": "安防效果时机",
        "question": """对手用数码兽攻击我，我的安防中翻出了一张有安防效果的卡。
这张卡的安防效果是'消灭攻击中的数码兽'。
请问这个效果能阻止我的安防被判定吗？""",
        "expected_features": ["timing", "ruling"]
    },
    {
        "name": "连锁规则",
        "question": """当两个诱发效果同时触发时，如何决定处理顺序？
回合玩家和非回合玩家各有一个效果。""",
        "expected_features": ["sequence", "ruling"]
    },
    {
        "name": "卡牌效果查询",
        "question": "BT23-032 土偶兽的效果是什么？",
        "expected_features": ["card"]
    }
]


def test_enhanced_judge():
    """测试增强版裁判"""
    from main_enhanced import EnhancedCardGameJudge
    
    judge = EnhancedCardGameJudge()
    
    print("=" * 80)
    print("增强版裁判系统测试")
    print("=" * 80)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"\n【问题】\n{test_case['question']}\n")
        
        try:
            answer = judge.query(
                test_case['question'],
                use_scenario_analysis=True
            )
            
            print("\n" + "=" * 80)
            print("【回答】")
            print("=" * 80)
            print(answer)
            
            # 质量检查
            print("\n【质量检查】")
            checks = {
                "结构化输出": any(kw in answer for kw in ["【", "】", "##", "1.", "2."]),
                "包含引用": "参考来源" in answer or "引用" in answer,
                "包含分析步骤": any(kw in answer for kw in ["步骤", "分析", "顺序"]),
                "明确结论": any(kw in answer for kw in ["结论", "因此", "所以"]),
            }
            
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check}")
            
        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            import traceback
            traceback.print_exc()


def test_query_processor():
    """测试增强查询处理器"""
    from app.enhanced_query_processor import enhanced_query_processor
    
    print("\n" + "=" * 80)
    print("查询处理器测试")
    print("=" * 80)
    
    test_query = "我方联展了 bt23-032 土偶兽，进化源中有天使兽，对方拉米亚兽消灭时会发生什么？"
    
    analysis = enhanced_query_processor.analyze_scenario(test_query)
    
    print(f"\n原始查询：{test_query}")
    print(f"\n分析结果:")
    print(f"  问题类型：{analysis['question_type']}")
    print(f"  涉及卡牌：{analysis['involved_cards']}")
    print(f"  效果时机：{analysis['effect_timings']}")
    print(f"  需要顺序分析：{analysis['needs_sequence_analysis']}")
    print(f"  需要连锁分析：{analysis['needs_chain_analysis']}")
    
    print(f"\n生成的搜索查询:")
    for query, qtype, weight in analysis['search_queries']:
        print(f"  [{weight:.1f}] ({qtype}) {query}")


def test_scenario_analyzer():
    """测试场面分析器"""
    from app.scenario_analyzer import scenario_analyzer
    
    print("\n" + "=" * 80)
    print("场面分析器测试")
    print("=" * 80)
    
    test_scenario = """我方联展了 bt23-032 土偶兽，把对方的数码兽退化成 bt24-016 拉米亚兽，
    并选择其主要阶段开始时攻击。土偶进化源中有 bt23-027 天使兽。"""
    
    # 模拟检索结果
    mock_context = [
        {
            "content": "当多个效果同时触发时，回合玩家的效果优先处理。",
            "metadata": {"title": "综合规则 3.2.1", "doc_type": "rule"},
            "doc_type": "rule"
        },
        {
            "content": "BT23-032 土偶兽：【攻击时】可以选择对方 1 只数码兽退化。",
            "metadata": {"title": "BT23-032 土偶兽", "doc_type": "card"},
            "doc_type": "card"
        }
    ]
    
    report = scenario_analyzer.generate_scenario_analysis(
        query=test_scenario,
        retrieved_context=mock_context
    )
    
    print("\n【分析报告】")
    print(report)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试增强版裁判系统")
    parser.add_argument("--judge", action="store_true", help="测试完整裁判系统")
    parser.add_argument("--processor", action="store_true", help="测试查询处理器")
    parser.add_argument("--analyzer", action="store_true", help="测试场面分析器")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    args = parser.parse_args()
    
    if args.all or (not any([args.judge, args.processor, args.analyzer])):
        test_query_processor()
        test_scenario_analyzer()
        test_enhanced_judge()
    else:
        if args.processor:
            test_query_processor()
        if args.analyzer:
            test_scenario_analyzer()
        if args.judge:
            test_enhanced_judge()
