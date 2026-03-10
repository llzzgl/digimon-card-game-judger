# -*- coding: utf-8 -*-
"""
检查官方QA数据的质量和统计信息
"""
import json
import re
from pathlib import Path
from collections import Counter


def inspect_qa_data(qa_file_path: str):
    """检查QA数据质量"""
    
    print("=" * 70)
    print("官方QA数据质量检查")
    print("=" * 70)
    
    # 读取数据
    qa_file_path = Path(qa_file_path)
    if not qa_file_path.exists():
        print(f"❌ 文件不存在: {qa_file_path}")
        return
    
    print(f"\n📂 文件: {qa_file_path}")
    print(f"📏 大小: {qa_file_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    with open(qa_file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"📊 总数: {len(qa_data)} 条QA")
    
    # 统计信息
    print("\n" + "=" * 70)
    print("📈 基本统计")
    print("=" * 70)
    
    # 统计有卡牌信息的QA
    with_card = sum(1 for qa in qa_data if qa.get("card_no"))
    print(f"• 关联卡牌的QA: {with_card} ({with_card/len(qa_data)*100:.1f}%)")
    
    # 统计问题和答案长度
    question_lengths = [len(qa.get("question", "")) for qa in qa_data]
    answer_lengths = [len(qa.get("answer", "")) for qa in qa_data]
    
    print(f"• 问题平均长度: {sum(question_lengths)/len(question_lengths):.1f} 字符")
    print(f"• 答案平均长度: {sum(answer_lengths)/len(answer_lengths):.1f} 字符")
    
    # 统计卡牌分布
    card_counter = Counter(qa.get("card_no", "") for qa in qa_data if qa.get("card_no"))
    print(f"• 涉及卡牌数: {len(card_counter)} 张")
    
    # 翻译质量检查
    print("\n" + "=" * 70)
    print("🔍 翻译质量检查")
    print("=" * 70)
    
    # 检查常见的机翻问题
    issues = {
        "日文残留_か": 0,
        "日文残留_和": 0,
        "日文残留_よ": 0,
        "日文残留_こ": 0,
        "混合_场合": 0,
        "混合_的时候": 0,
        "空问题": 0,
        "空答案": 0,
    }
    
    problem_samples = []
    
    for qa in qa_data:
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        
        if not question:
            issues["空问题"] += 1
        if not answer:
            issues["空答案"] += 1
        
        text = question + answer
        
        if "か" in text:
            issues["日文残留_か"] += 1
            if len(problem_samples) < 3:
                problem_samples.append(("日文残留_か", question[:50]))
        
        if re.search(r'[^\u4e00-\u9fff]和[^\u4e00-\u9fff]', text):
            issues["日文残留_和"] += 1
            if len(problem_samples) < 3:
                problem_samples.append(("日文残留_和", question[:50]))
        
        if "よ" in text or "って" in text:
            issues["日文残留_よ"] += 1
        
        if "こ和" in text:
            issues["日文残留_こ"] += 1
        
        if "场合" in text:
            issues["混合_场合"] += 1
        
        if "的时候" in text:
            issues["混合_的时候"] += 1
    
    print("\n发现的问题:")
    for issue, count in issues.items():
        if count > 0:
            percentage = count / len(qa_data) * 100
            status = "⚠️" if percentage > 10 else "ℹ️"
            print(f"{status} {issue}: {count} ({percentage:.1f}%)")
    
    if problem_samples:
        print("\n问题示例:")
        for issue_type, sample in problem_samples[:3]:
            print(f"  [{issue_type}] {sample}...")
    
    # 数据示例
    print("\n" + "=" * 70)
    print("📝 数据示例")
    print("=" * 70)
    
    for i, qa in enumerate(qa_data[:3], 1):
        print(f"\n【示例 {i}】")
        print(f"QA编号: {qa.get('qa_number', 'N/A')}")
        if qa.get('card_no'):
            print(f"卡牌: {qa.get('card_no')} {qa.get('card_name', '')}")
        print(f"问题: {qa.get('question', '')[:100]}...")
        print(f"答案: {qa.get('answer', '')[:100]}...")
    
    # 建议
    print("\n" + "=" * 70)
    print("💡 建议")
    print("=" * 70)
    
    total_issues = sum(v for k, v in issues.items() if "日文残留" in k or "混合" in k)
    issue_rate = total_issues / len(qa_data) * 100
    
    if issue_rate > 30:
        print("⚠️ 翻译质量较差，建议:")
        print("   1. 使用 translate_qa_with_llm.py 重新翻译")
        print("   2. 或使用 translate_qa_local.py 本地翻译")
        print("   3. 然后再处理用于微调")
    elif issue_rate > 10:
        print("ℹ️ 翻译质量一般，建议:")
        print("   1. 可以直接使用，但效果可能受影响")
        print("   2. 或先改进翻译质量")
        print("   3. 运行 process_official_qa_cn.py 会自动清理部分问题")
    else:
        print("✅ 翻译质量良好，可以直接使用")
        print("   运行 process_official_qa_cn.py 处理数据")
    
    print("\n下一步:")
    print("   cd card_game_judge/finetune")
    print("   python process_official_qa_cn.py")
    print("   python collect_all_data.py")
    
    print("\n" + "=" * 70)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查官方QA数据质量")
    parser.add_argument("--input", type=str,
                        default="../card_game_QA_manger/official_qa_cn.json",
                        help="QA JSON文件路径")
    
    args = parser.parse_args()
    
    input_path = Path(__file__).parent / args.input
    inspect_qa_data(str(input_path))


if __name__ == "__main__":
    main()
