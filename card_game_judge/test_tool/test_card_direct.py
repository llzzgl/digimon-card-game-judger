"""直接测试卡牌搜索（不加载 embedding 模型）"""
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
from app.models import DocumentType

# 使用项目根目录的 data/chroma_db
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

question = "内存值为0时，支付4内存，在我方五级紫色数码兽上进化BT20-079幽灵巫师兽，对面场上有BT23-058颅骨兽，该怎么处理效果？"

print("=== 提取卡牌编号 ===")
card_numbers = query_processor.extract_card_numbers(question)
print(f"卡牌编号: {card_numbers}")

print("\n=== 精确搜索卡牌 ===")
client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection("card_game_rule")
all_docs = collection.get(include=["documents", "metadatas"])

for card_no in card_numbers:
    print(f"\n搜索: {card_no}")
    card_no_upper = card_no.upper()
    
    found = []
    for i, doc in enumerate(all_docs["documents"]):
        if f"【{card_no_upper}】" in doc or f"【{card_no_upper}_" in doc:
            found.append((doc, all_docs["metadatas"][i]))
    
    print(f"找到 {len(found)} 条结果")
    
    if found:
        doc, meta = found[0]
        # 翻译
        translated = terminology_translator.translate_result_to_chinese(doc)
        print(f"\n标题: {meta.get('title', 'N/A')}")
        print(f"内容 (已翻译):\n{translated[:600]}...")
