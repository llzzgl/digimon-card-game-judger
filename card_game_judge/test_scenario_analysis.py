# -*- coding: utf-8 -*-
"""
测试场面分析能力
对比改进前后的效果
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from app.llm_service_finetuned import get_finetuned_llm_service
from app.vector_store import vector_store


def test_scenario_analysis():
    """测试场面分析"""
    
    # 测试问题
    test_question = """我方联展了bt23-032土偶兽，把对方的数码兽退化成bt24-016拉米亚兽，并选择其主要阶段开始时攻击。
土偶进化源中有bt23-027天使兽和bt23-050甲龙兽。
对方拉米亚进化源中有bt21-001基基兽。
此时移交回合后会发生什么？"""
    
    print("=" * 80)
    print("场面分析能力测试")
    print("=" * 80)
    print(f"\n【测试问题】\n{test_question}\n")
    
    # 步骤1：检索相关文档
    print("步骤1：检索相关文档...")
    search_results = vector_store.search(test_question, top_k=5)
    
    print(f"找到 {len(search_results)} 个相关文档：")
    for i, doc in enumerate(search_results, 1):
        title = doc['metadata'].get('title', '未知')
        score = doc.get('score', 0)
        print(f"  {i}. {title} (相似度: {score:.3f})")
    
    # 步骤2：调用微调模型
    print("\n步骤2：调用微调模型生成回答...")
    print("-" * 80)
    
    try:
        llm_service = get_finetuned_llm_service()
        
        def log_callback(msg):
            print(f"  {msg}")
        
        answer = llm_service.generate_answer(
            question=test_question,
            context_docs=search_results,
            log_callback=log_callback
        )
        
        print("\n" + "=" * 80)
        print("【模型回答】")
        print("=" * 80)
        print(answer)
        print("=" * 80)
        
        # 分析回答质量
        print("\n【回答质量分析】")
        
        quality_checks = {
            "包含卡牌效果分析": any(keyword in answer for keyword in ["涉及的卡牌", "卡牌效果", "BT23-032", "BT24-016"]),
            "包含规则引用": any(keyword in answer for keyword in ["规则", "条款", "规则参考"]),
            "包含处理顺序": any(keyword in answer for keyword in ["处理顺序", "顺序", "先", "后", "然后"]),
            "包含明确结论": any(keyword in answer for keyword in ["结论", "因此", "所以", "最终"]),
            "结构化输出": any(keyword in answer for keyword in ["【", "】", "1.", "2.", "•"])
        }
        
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        passed_count = sum(quality_checks.values())
        total_count = len(quality_checks)
        score = (passed_count / total_count) * 100
        
        print(f"\n总体评分: {passed_count}/{total_count} ({score:.0f}%)")
        
        if score >= 80:
            print("✅ 回答质量良好")
        elif score >= 60:
            print("⚠️ 回答质量一般，建议添加更多场面分析训练数据")
        else:
            print("❌ 回答质量较差，需要添加场面分析训练数据并重新训练")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_scenarios():
    """测试多个场面"""
    
    test_cases = [
        {
            "name": "复杂场面分析",
            "question": """我方联展了bt23-032土偶兽，把对方的数码兽退化成bt24-016拉米亚兽，并选择其主要阶段开始时攻击。
土偶进化源中有bt23-027天使兽和bt23-050甲龙兽。对方拉米亚进化源中有bt21-001基基兽。
此时移交回合后会发生什么？"""
        },
        {
            "name": "效果触发时机",
            "question": "对手用数码兽攻击我，我的安防中翻出了一张有安防效果的卡。这张卡的安防效果是'消灭攻击中的数码兽'。请问这个效果能阻止我的安防被判定吗？"
        },
        {
            "name": "效果处理顺序",
            "question": "我的数码兽攻击对手，对战中消灭了对手的数码兽。我的数码兽有≪贯通≫效果，同时有【消灭对手数码兽时】的效果。请问这两个效果如何处理？"
        }
    ]
    
    print("=" * 80)
    print("多场面测试")
    print("=" * 80)
    
    llm_service = get_finetuned_llm_service()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"\n【问题】\n{test_case['question']}\n")
        
        # 检索
        search_results = vector_store.search(test_case['question'], top_k=3)
        
        # 生成回答
        try:
            answer = llm_service.generate_answer(
                question=test_case['question'],
                context_docs=search_results
            )
            
            print(f"【回答】\n{answer}\n")
            
        except Exception as e:
            print(f"❌ 失败: {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试场面分析能力")
    parser.add_argument("--multiple", action="store_true", help="测试多个场面")
    args = parser.parse_args()
    
    if args.multiple:
        test_multiple_scenarios()
    else:
        test_scenario_analysis()
