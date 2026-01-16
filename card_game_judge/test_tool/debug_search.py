"""调试搜索问题"""
import os
import sys
sys.path.insert(0, '.')

os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import warnings
warnings.filterwarnings('ignore')

from chromadb.config import Settings
import chromadb
from app.query_processor import query_processor
from app.terminology_translator import terminology_translator

# 使用项目根目录的 data/chroma_db
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

# 测试问题
question = "内存值为0时，支付4内存，在我方五级紫色数码兽上进化BT20-073，对面场上有BT23-058，该怎么处理效果？"

print("=== 1. 提取卡牌编号 ===")
card_numbers = query_processor.extract_card_numbers(question)
print(f"提取到: {card_numbers}")

print("\n=== 2. 搜索每张卡牌 ===")
client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection("card_game_rule")
all_docs = collection.get(include=["documents", "metadatas"])
print(f"数据库总文档数: {len(all_docs['documents'])}")

for card_no in card_numbers:
    print(f"\n--- 搜索: {card_no} ---")
    card_no_upper = card_no.upper()
    
    found_count = 0
    for i, doc in enumerate(all_docs["documents"]):
        # 检查多种格式
        patterns = [
            f"【{card_no_upper}】",
            f"【{card_no_upper}_",
            f"card_no\": \"{card_no_upper}\"",
        ]
        
        for pattern in patterns:
            if pattern in doc:
                found_count += 1
                if found_count <= 2:  # 只显示前2条
                    translated = terminology_translator.translate_result_to_chinese(doc)
                    print(f"\n找到 (模式: {pattern}):")
                    print(f"标题: {all_docs['metadatas'][i].get('title', 'N/A')}")
                    print(f"内容前400字:\n{translated[:400]}")
                break
    
    print(f"\n总共找到 {found_count} 条匹配")
