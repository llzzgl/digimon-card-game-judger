"""测试中文卡牌搜索"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vector_store import vector_store

# 测试卡牌编号搜索
test_cards = ["BT23-032", "BT23-027", "BT23-050"]

print("=" * 60)
print("测试中文卡牌搜索")
print("=" * 60)

for card_no in test_cards:
    print(f"\n搜索: {card_no}")
    results = vector_store.search_by_card_number(card_no)
    
    if results:
        result = results[0]
        print(f"来源: {result['metadata'].get('source', 'unknown')}")
        print(f"标题: {result['metadata'].get('title', 'unknown')}")
        print(f"内容预览:")
        print("-" * 40)
        print(result['content'][:500])
        print("-" * 40)
    else:
        print("未找到")

print("\n" + "=" * 60)
print(f"中文卡牌数据总数: {len(vector_store._cn_cards)}")
print("=" * 60)
