"""
测试翻译后的QA数据
验证数据格式和内容正确性
"""
import json
from pathlib import Path


def test_translated_qa():
    """测试翻译后的QA数据"""
    
    qa_path = Path(__file__).parent / "official_qa_cn.json"
    
    if not qa_path.exists():
        print("❌ 错误: 找不到翻译文件 official_qa_cn.json")
        print("请先运行: python translate_qa_local.py")
        return False
    
    # 加载数据
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_list = json.load(f)
    
    print("="*60)
    print("翻译数据测试")
    print("="*60)
    
    # 基本统计
    print(f"\n✓ 成功加载 {len(qa_list)} 条QA")
    
    # 检查必需字段
    required_fields = ['id', 'question', 'answer', 'language']
    missing_fields = []
    
    for i, qa in enumerate(qa_list[:100]):  # 检查前100条
        for field in required_fields:
            if field not in qa:
                missing_fields.append((i, field))
    
    if missing_fields:
        print(f"❌ 发现缺失字段: {len(missing_fields)} 处")
        for idx, field in missing_fields[:5]:
            print(f"   QA #{idx}: 缺少 '{field}'")
    else:
        print(f"✓ 所有必需字段完整")
    
    # 检查语言标记
    zh_count = sum(1 for qa in qa_list if qa.get('language') == 'zh-cn')
    print(f"✓ 中文标记: {zh_count}/{len(qa_list)} ({zh_count*100//len(qa_list)}%)")
    
    # 检查原始字段保留
    with_original = sum(1 for qa in qa_list if 'question_original' in qa)
    print(f"✓ 保留原始问题: {with_original}/{len(qa_list)} ({with_original*100//len(qa_list)}%)")
    
    # 检查关键术语
    print("\n" + "="*60)
    print("关键术语检查")
    print("="*60)
    
    key_terms = {
        '【登场时】': 0,
        '【进化时】': 0,
        '【攻击时】': 0,
        '【安防】': 0,
        '数码宝贝': 0,
        '驯兽师': 0,
        '休眠': 0,
        '激活': 0,
    }
    
    for qa in qa_list:
        text = qa.get('question', '') + ' ' + qa.get('answer', '')
        for term in key_terms:
            if term in text:
                key_terms[term] += 1
    
    for term, count in key_terms.items():
        if count > 0:
            print(f"✓ {term:15s}: {count:4d} 次")
        else:
            print(f"⚠ {term:15s}: 未找到")
    
    # 显示示例
    print("\n" + "="*60)
    print("数据示例")
    print("="*60)
    
    # 找一个包含卡号的QA
    example = None
    for qa in qa_list:
        if qa.get('card_no') and '【登场时】' in qa.get('question', ''):
            example = qa
            break
    
    if not example:
        example = qa_list[0]
    
    print(f"\nQA编号: {example.get('qa_number', 'N/A')}")
    if example.get('card_no'):
        print(f"卡号: {example.get('card_no')}")
        print(f"卡名: {example.get('card_name', 'N/A')}")
    
    print(f"\n问题:")
    print(example.get('question', '')[:200])
    
    print(f"\n答案:")
    print(example.get('answer', '')[:200])
    
    if 'question_original' in example:
        print(f"\n原始问题:")
        print(example.get('question_original', '')[:200])
    
    # 数据质量评分
    print("\n" + "="*60)
    print("数据质量评分")
    print("="*60)
    
    score = 0
    max_score = 5
    
    # 1. 数据完整性
    if len(qa_list) > 4000:
        score += 1
        print("✓ 数据量充足 (>4000条)")
    else:
        print("⚠ 数据量不足")
    
    # 2. 字段完整性
    if not missing_fields:
        score += 1
        print("✓ 字段完整")
    else:
        print("⚠ 部分字段缺失")
    
    # 3. 语言标记
    if zh_count > len(qa_list) * 0.95:
        score += 1
        print("✓ 语言标记正确")
    else:
        print("⚠ 语言标记不完整")
    
    # 4. 术语替换
    if sum(key_terms.values()) > 1000:
        score += 1
        print("✓ 术语替换成功")
    else:
        print("⚠ 术语替换不足")
    
    # 5. 原始数据保留
    if with_original > len(qa_list) * 0.95:
        score += 1
        print("✓ 原始数据已保留")
    else:
        print("⚠ 原始数据保留不完整")
    
    print(f"\n总分: {score}/{max_score}")
    
    if score >= 4:
        print("✅ 数据质量优秀，可以直接使用！")
        return True
    elif score >= 3:
        print("⚠️ 数据质量良好，建议检查后使用")
        return True
    else:
        print("❌ 数据质量不佳，建议重新翻译")
        return False


def main():
    """主函数"""
    success = test_translated_qa()
    
    if success:
        print("\n" + "="*60)
        print("后续步骤")
        print("="*60)
        print("\n1. 查看详细分析:")
        print("   python analyze_translation.py")
        print("\n2. 集成到系统:")
        print("   python copy_to_finetune.py")
        print("\n3. 构建向量数据库:")
        print("   cd ..")
        print("   python rebuild_vectordb.py")


if __name__ == "__main__":
    main()
