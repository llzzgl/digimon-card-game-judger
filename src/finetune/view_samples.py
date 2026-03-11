# -*- coding: utf-8 -*-
"""查看训练数据示例"""
import json
from pathlib import Path

def view_samples():
    data_file = Path(__file__).parent / "training_data" / "dtcg_finetune_data.jsonl"
    
    print("=" * 60)
    print("训练数据示例")
    print("=" * 60)
    
    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    
    print(f"\n总数据量: {len(data)} 条\n")
    
    # 按来源分类
    sources = {}
    for item in data:
        # 从 instruction 推断来源
        if "规则专家" in item["instruction"] and "规则" in item["input"]:
            source = "规则书"
        elif "卡牌数据专家" in item["instruction"]:
            source = "卡牌数据"
        elif "官方裁定专家" in item["instruction"]:
            source = "官方Q&A"
        else:
            source = "其他"
        
        if source not in sources:
            sources[source] = []
        sources[source].append(item)
    
    # 显示每种来源的示例
    for source, items in sources.items():
        print(f"\n{'=' * 60}")
        print(f"【{source}】示例 (共 {len(items)} 条)")
        print('=' * 60)
        
        # 显示前3个示例
        for i, item in enumerate(items[:3], 1):
            print(f"\n示例 {i}:")
            print(f"问题: {item['input']}")
            print(f"答案: {item['output'][:200]}...")
            print()

if __name__ == "__main__":
    view_samples()
