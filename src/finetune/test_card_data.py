# -*- coding: utf-8 -*-
"""
测试卡牌数据加载功能
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DTCGDataCollector


def test_card_data_loading():
    """测试卡牌数据加载"""
    print("=" * 60)
    print("测试卡牌数据加载功能")
    print("=" * 60)
    
    # 初始化收集器
    collector = DTCGDataCollector(output_dir="training_data")
    
    # 加载卡牌数据
    card_data_path = Path(__file__).parent.parent.parent / "digimon_card_data_chiness" / "digimon_cards_cn.json"
    
    # 如果相对路径不存在，尝试绝对路径
    if not card_data_path.exists():
        card_data_path = Path("D:/niii/zzl/LLMProject/digimon_card_data_chiness/digimon_cards_cn.json")
    
    if not card_data_path.exists():
        print(f"❌ 卡牌数据文件不存在: {card_data_path}")
        return
    
    print(f"\n📥 加载卡牌数据: {card_data_path}")
    count = collector.load_card_data(str(card_data_path))
    
    print(f"\n✅ 生成了 {count} 条卡牌相关问答")
    
    # 显示统计
    collector.print_statistics()
    
    # 显示一些示例
    print("\n" + "=" * 60)
    print("📝 问答示例")
    print("=" * 60)
    
    if collector.card_qa_pairs:
        for i, qa in enumerate(collector.card_qa_pairs[:5], 1):
            print(f"\n【示例 {i}】")
            print(f"问题: {qa.input}")
            print(f"回答: {qa.output[:200]}...")
            print(f"来源: {qa.source}")
            print(f"标签: {', '.join(qa.tags)}")
    
    # 导出测试数据
    print("\n" + "=" * 60)
    print("💾 导出测试数据")
    print("=" * 60)
    
    output_file = collector.export_jsonl("test_card_data.jsonl")
    print(f"✅ 已导出到: {output_file}")


if __name__ == "__main__":
    test_card_data_loading()
