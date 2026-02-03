"""
翻译质量分析脚本
分析翻译后的QA数据，提供统计信息
"""
import json
import re
from pathlib import Path
from collections import Counter


def analyze_translation(qa_path: str):
    """分析翻译后的QA数据"""
    
    # 加载数据
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_list = json.load(f)
    
    print("="*60)
    print("翻译数据分析报告")
    print("="*60)
    print(f"\n总QA条数: {len(qa_list)}")
    
    # 统计有卡号的QA
    with_card_no = sum(1 for qa in qa_list if qa.get('card_no'))
    print(f"包含卡号的QA: {with_card_no} ({with_card_no*100//len(qa_list)}%)")
    
    # 统计卡牌名称替换情况
    card_name_replaced = 0
    for qa in qa_list:
        if qa.get('card_name') and qa.get('card_name_original'):
            if qa['card_name'] != qa['card_name_original']:
                card_name_replaced += 1
    
    print(f"卡牌名称已替换: {card_name_replaced}")
    
    # 检查日文残留
    print("\n" + "="*60)
    print("日文残留分析")
    print("="*60)
    
    # 常见日文字符
    hiragana_pattern = r'[\u3040-\u309F]'  # 平假名
    katakana_pattern = r'[\u30A0-\u30FF]'  # 片假名
    
    questions_with_hiragana = 0
    answers_with_hiragana = 0
    questions_with_katakana = 0
    answers_with_katakana = 0
    
    for qa in qa_list:
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        if re.search(hiragana_pattern, question):
            questions_with_hiragana += 1
        if re.search(hiragana_pattern, answer):
            answers_with_hiragana += 1
        if re.search(katakana_pattern, question):
            questions_with_katakana += 1
        if re.search(katakana_pattern, answer):
            answers_with_katakana += 1
    
    print(f"\n问题中包含平假名: {questions_with_hiragana} ({questions_with_hiragana*100//len(qa_list)}%)")
    print(f"答案中包含平假名: {answers_with_hiragana} ({answers_with_hiragana*100//len(qa_list)}%)")
    print(f"问题中包含片假名: {questions_with_katakana} ({questions_with_katakana*100//len(qa_list)}%)")
    print(f"答案中包含片假名: {answers_with_katakana} ({answers_with_katakana*100//len(qa_list)}%)")
    
    # 统计关键术语出现频率
    print("\n" + "="*60)
    print("关键术语统计（前20）")
    print("="*60)
    
    term_counter = Counter()
    key_terms = [
        '【登场时】', '【进化时】', '【攻击时】', '【安防】',
        '数码宝贝', '驯兽师', '选项', '数码蛋',
        '休眠', '激活', '消灭', '废弃区',
        '对手', '自己', '可以', '不可以'
    ]
    
    for qa in qa_list:
        text = qa.get('question', '') + ' ' + qa.get('answer', '')
        for term in key_terms:
            count = text.count(term)
            if count > 0:
                term_counter[term] += count
    
    for term, count in term_counter.most_common(20):
        print(f"{term:15s}: {count:5d}")
    
    # 查找未替换的常见日文词
    print("\n" + "="*60)
    print("常见未翻译日文词（前20）")
    print("="*60)
    
    # 提取所有平假名词
    hiragana_words = Counter()
    for qa in qa_list:
        text = qa.get('question', '') + ' ' + qa.get('answer', '')
        words = re.findall(r'[\u3040-\u309F]+', text)
        hiragana_words.update(words)
    
    for word, count in hiragana_words.most_common(20):
        print(f"{word:15s}: {count:5d}")
    
    # 示例展示
    print("\n" + "="*60)
    print("翻译示例（随机5条）")
    print("="*60)
    
    import random
    samples = random.sample(qa_list, min(5, len(qa_list)))
    
    for i, qa in enumerate(samples, 1):
        print(f"\n--- 示例 {i} ---")
        print(f"QA编号: {qa.get('qa_number', 'N/A')}")
        if qa.get('card_no'):
            print(f"卡号: {qa.get('card_no')}")
        print(f"\n原始问题:\n{qa.get('question_original', '')[:100]}...")
        print(f"\n翻译后:\n{qa.get('question', '')[:100]}...")
        print(f"\n原始答案:\n{qa.get('answer_original', '')[:100]}...")
        print(f"\n翻译后:\n{qa.get('answer', '')[:100]}...")


def main():
    """主函数"""
    base_dir = Path(__file__).parent
    qa_path = base_dir / "official_qa_cn.json"
    
    if not qa_path.exists():
        print(f"错误: 找不到文件 {qa_path}")
        print("请先运行 translate_qa_local.py 生成翻译文件")
        return
    
    analyze_translation(str(qa_path))


if __name__ == "__main__":
    main()
