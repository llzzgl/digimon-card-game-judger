"""测试卡牌精确搜索"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, '.')

from app.vector_store import vector_store
from app.query_processor import query_processor

question = "内存值为0时，支付4内存，在我方五级紫色数码兽上进化BT20-079幽灵巫师兽，对面场上有BT23-058颅骨兽，该怎么处理效果？"

print("=== 提取卡牌编号 ===")
card_numbers = query_processor.extract_card_numbers(question)
print(f"卡牌编号: {card_numbers}")

print("\n=== 精确搜索卡牌 ===")
for card_no in card_numbers:
    print(f"\n搜索: {card_no}")
    results = vector_store.search_by_card_number(card_no, translate_result=True)
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results):
        print(f"\n[{i+1}] 内容:")
        print(r['content'][:500])
        print("...")
