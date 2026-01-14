"""测试 API 的检索逻辑"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, '.')

from app.query_processor import query_processor
from app.vector_store import vector_store

question = "内存值为0时，支付4内存，在我方五级紫色数码兽上进化BT20-079幽灵巫师兽，对面场上有BT23-058颅骨兽，该怎么处理效果？"

print("=== 查询分析 ===")
card_numbers = query_processor.extract_card_numbers(question)
print(f"提取的卡牌编号: {card_numbers}")

print("\n=== 卡牌检索测试 ===")
for card_no in card_numbers:
    print(f"\n检索: {card_no}")
    results = vector_store.search(
        query=card_no,
        top_k=2,
        translate_query=False,
        translate_result=False
    )
    if results:
        for i, r in enumerate(results):
            print(f"  [{i+1}] 分数: {r['score']:.4f}")
            print(f"      内容: {r['content'][:150]}...")
    else:
        print("  无结果")

print("\n=== 规则检索测试 ===")
results = vector_store.search(
    query=question,
    top_k=3,
    translate_query=True,
    translate_result=False
)
for i, r in enumerate(results):
    print(f"[{i+1}] 分数: {r['score']:.4f}")
    print(f"    标题: {r['metadata'].get('title', 'N/A')}")
    print(f"    内容: {r['content'][:100]}...")
