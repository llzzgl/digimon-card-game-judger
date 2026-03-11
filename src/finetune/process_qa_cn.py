# -*- coding: utf-8 -*-
"""
处理中文官方QA数据，转换为微调训练格式
改进版 - 更好的文本清理
"""
import json
import sys
import re
from pathlib import Path
from typing import List, Dict

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DTCGDataCollector


def clean_qa_text(text: str) -> str:
    """清理QA文本中的问题 - 改进版"""
    if not text:
        return text
    
    # 移除更新日期标记
    text = re.sub(r'\n\d{4}/\d{2}/\d{2}\s*更新', '', text)
    
    # 清理常见的机翻问题 - 扩展版
    replacements = {
        # 日文残留
        'か？': '吗？',
        'か。': '吗。',
        'か、': '吗，',
        '和して': '作为',
        'よって': '通过',
        'こ和': '这',
        'って': '',
        '的场合': '的情况',
        '场合': '情况',
        '的时候': '时',
        '了时': '时',
        '検查': '检查',
        '発挥': '发挥',
        '効果': '效果',
        '数码宝贝也': '数码宝贝都',
        '也休眠': '都可以休眠',
        '也可以': '都可以',
        '可以吗？': '吗？',
        '不可以': '不能',
        '登场させ': '登场',
        '消灭させ': '消灭',
        '発動': '发动',
        '触发了': '触发',
        '次合': '回合',
        'タイミング': '时机',
        '待ち': '',
        '从发动': '开始发动',
        '方的': '方',
        '持た没有': '没有',
        '仅存在': '存在',
        '选择无法': '无法选择',
        '消灭し没有': '没有消灭',
        '攻击終了': '攻击结束',
        '対戦': '对战',
        '勝った': '获胜',
        '負けた': '失败',
        '存在的情况': '的情况',
        '了的情况': '的情况',
        '的情况下': '时',
        '会怎样？': '会如何处理？',
        '按什么顺序': '按照什么顺序',
        '发挥か': '发挥',
        '触发か': '触发',
        '可以か': '可以',
        '不可以か': '不可以',
        '登场か': '登场',
        '消灭か': '消灭',
        '効果す': '效果',
        '効果な': '效果',
        '効果和': '效果',
        '和、': '，',
        '、和': '，',
        '。和': '。',
        '和。': '。',
        '被检查场合': '被检查时',
        '不会立即发动': '不会立即发动',
        '其他的触发了效果': '其他触发的效果',
        '玩家方的效果从发动': '玩家方的效果开始发动',
        '休眠可以': '可以休眠',
        '攻击可以': '可以攻击',
        '登场可以': '可以登场',
        '消灭可以': '可以消灭',
        '発揮': '发挥',
        '発動': '发动',
        '発生': '发生',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 清理多余的标点
    text = re.sub(r'[，,]{2,}', '，', text)
    text = re.sub(r'[。\.]{2,}', '。', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def process_official_qa_cn(qa_file_path: str, output_dir: str = "origin_data"):
    """
    处理中文官方QA数据
    
    Args:
        qa_file_path: 官方QA JSON文件路径
        output_dir: 输出目录
    """
    print("=" * 70)
    print("处理中文官方QA数据 - 改进版")
    print("=" * 70)
    
    # 读取QA数据
    qa_file_path = Path(qa_file_path)
    if not qa_file_path.exists():
        print(f"❌ QA文件不存在: {qa_file_path}")
        return
    
    print(f"\n📥 读取QA文件: {qa_file_path}")
    with open(qa_file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"✅ 读取了 {len(qa_data)} 条QA数据")
    
    # 初始化数据收集器
    collector = DTCGDataCollector(output_dir=output_dir)
    
    # 转换QA数据格式
    print("\n📝 转换并清理QA数据...")
    converted_qa = []
    skipped_count = 0
    cleaned_count = 0
    
    for item in qa_data:
        question_raw = item.get("question", "")
        answer_raw = item.get("answer", "")
        
        # 清理文本
        question = clean_qa_text(question_raw)
        answer = clean_qa_text(answer_raw)
        
        # 统计清理效果
        if question != question_raw or answer != answer_raw:
            cleaned_count += 1
        
        # 跳过空问答
        if not question or not answer:
            skipped_count += 1
            continue
        
        # 构建完整的答案（包含卡牌信息）
        full_answer = answer
        
        # 如果有卡牌信息，添加到答案前面
        card_no = item.get("card_no", "")
        card_name = item.get("card_name", "")
        
        if card_no and card_name:
            full_answer = f"【{card_no}】{card_name}\n\n{answer}"
        elif card_no:
            full_answer = f"【{card_no}】\n\n{answer}"
        
        # 添加来源信息
        qa_number = item.get("qa_number", "")
        if qa_number:
            full_answer += f"\n\n（官方Q&A #{qa_number}）"
        
        converted_item = {
            "question": question,
            "answer": full_answer,
            "card_no": card_no,
            "card_name": card_name,
            "source": f"official_qa_{item.get('source', 'unknown')}",
            "date": item.get("scraped_at", ""),
            "qa_number": qa_number,
            "original_question": item.get("question_original", ""),
            "original_answer": item.get("answer_original", "")
        }
        
        converted_qa.append(converted_item)
    
    print(f"✅ 转换了 {len(converted_qa)} 条QA")
    print(f"🧹 清理了 {cleaned_count} 条QA的文本")
    if skipped_count > 0:
        print(f"⚠️ 跳过了 {skipped_count} 条空QA")
    
    # 保存清理后的QA数据到origin_data（供collect_all_data.py使用）
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cleaned_qa_path = output_path / "official_qa_cn_cleaned.json"
    with open(cleaned_qa_path, 'w', encoding='utf-8') as f:
        json.dump(converted_qa, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存清理后的QA到: {cleaned_qa_path}")
    
    # 同时生成一个简化版本供collect_all_data.py直接使用
    simplified_qa = []
    for item in converted_qa:
        simplified_qa.append({
            "question": item["question"],
            "answer": item["answer"],
            "card_no": item.get("card_no", ""),
            "card_name": item.get("card_name", ""),
            "source": "official_qa",
            "date": item.get("date", "")
        })
    
    simplified_path = output_path / "official_qa.json"
    with open(simplified_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_qa, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存简化版QA到: {simplified_path}")
    
    print("\n" + "=" * 70)
    print("✅ 处理完成！")
    print("=" * 70)
    print(f"\n📊 总计: {len(converted_qa)} 条官方QA数据")
    print(f"📁 输出文件:")
    print(f"   • {cleaned_qa_path} (完整版)")
    print(f"   • {simplified_path} (简化版，供collect_all_data.py使用)")
    
    print("\n🚀 下一步:")
    print("   python collect_all_data.py")
    print("   这将整合规则书、QA和卡牌数据生成完整的训练数据集")
    
    return converted_qa


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="处理中文官方QA数据")
    parser.add_argument("--input", type=str,
                        default="official_qa_cn.json",
                        help="输入的QA JSON文件路径")
    parser.add_argument("--output-dir", type=str,
                        default="origin_data",
                        help="输出目录")
    
    args = parser.parse_args()
    
    # 处理QA数据
    input_path = Path(__file__).parent / args.input
    process_official_qa_cn(str(input_path), args.output_dir)


if __name__ == "__main__":
    main()
