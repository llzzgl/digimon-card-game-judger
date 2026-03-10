# -*- coding: utf-8 -*-
"""
完整的 DTCG 微调数据收集脚本
整合规则书、官方Q&A和卡牌数据
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DTCGDataCollector


def collect_all_training_data():
    """收集所有训练数据"""
    print("=" * 60)
    print("DTCG 微调数据完整收集")
    print("=" * 60)
    
    # 初始化收集器
    collector = DTCGDataCollector(output_dir="training_data")
    
    # 1. 从规则书提取
    print("\n【步骤 1】从规则书提取问答...")
    rulebook_path = Path(__file__).parent / "origin_data" / "rulebook.txt"
    
    if rulebook_path.exists():
        print(f"📖 找到规则书: {rulebook_path}")
        rule_count = collector.extract_from_rulebook(str(rulebook_path))
        print(f"✅ 从规则书提取了 {rule_count} 条问答")
    else:
        print(f"⚠️ 规则书不存在: {rulebook_path}")
        print("   请将规则书文件放置到 origin_data/rulebook.txt")
        print("   跳过规则书数据收集")
    
    # 2. 加载官方 Q&A（如果有）
    print("\n【步骤 2】加载官方 Q&A...")
    official_qa_path = Path(__file__).parent / "origin_data" / "official_qa.json"
    
    if official_qa_path.exists():
        qa_count = collector.load_official_qa_from_file(str(official_qa_path))
        print(f"✅ 加载了 {qa_count} 条官方 Q&A")
    else:
        print(f"⚠️ 官方 Q&A 文件不存在: {official_qa_path}")
        print("   请将官方 Q&A 文件放置到 origin_data/official_qa.json")
        print("   跳过官方 Q&A 数据收集")
    
    # 3. 加载卡牌数据
    print("\n【步骤 3】加载卡牌数据...")
    card_data_path = Path(__file__).parent / "origin_data" / "cards.json"
    
    if card_data_path.exists():
        card_count = collector.load_card_data(str(card_data_path))
        print(f"✅ 从卡牌数据生成了 {card_count} 条问答")
    else:
        print(f"⚠️ 卡牌数据文件不存在: {card_data_path}")
        print("   请将卡牌数据文件放置到 origin_data/cards.json")
        print("   跳过卡牌数据收集")
    
    # 4. 显示统计
    print("\n【步骤 4】数据统计")
    collector.print_statistics()
    
    # 5. 导出数据
    print("\n【步骤 5】导出训练数据")
    stats = collector.get_statistics()
    
    if stats['total_count'] > 0:
        # 导出 JSONL 格式（用于微调）
        jsonl_path = collector.export_jsonl("dtcg_finetune_data.jsonl")
        print(f"✅ JSONL 格式: {jsonl_path}")
        
        # 导出 JSON 格式（便于查看）
        json_path = collector.export_json("dtcg_finetune_data.json")
        print(f"✅ JSON 格式: {json_path}")
        
        # 导出对话格式
        conv_path = collector.export_conversation_format("dtcg_conversation.jsonl")
        print(f"✅ 对话格式: {conv_path}")
        
        print("\n" + "=" * 60)
        print("✅ 数据收集完成！")
        print("=" * 60)
        print(f"\n📊 总计生成 {stats['total_count']} 条训练数据")
        print(f"   • 规则书问答: {stats['rule_qa_count']}")
        print(f"   • 官方 Q&A: {stats['official_qa_count']}")
        print(f"   • 卡牌数据问答: {stats['card_qa_count']}")
        print(f"   • 自定义问答: {stats['custom_qa_count']}")
        
        print("\n📁 输出文件:")
        print(f"   • {jsonl_path}")
        print(f"   • {json_path}")
        print(f"   • {conv_path}")
        
        print("\n🚀 下一步:")
        print("   使用以下命令开始微调:")
        print(f"   python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl")
        
    else:
        print("\n⚠️ 没有数据可导出")
        print("   请检查规则书、Q&A 文件和卡牌数据是否存在")


if __name__ == "__main__":
    collect_all_training_data()
