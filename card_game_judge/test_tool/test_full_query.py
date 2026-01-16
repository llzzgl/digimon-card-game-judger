"""完整测试查询流程"""
import os
import sys
sys.path.insert(0, '.')

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import warnings
warnings.filterwarnings('ignore')

from app.query_processor import query_processor
from app.terminology_translator import terminology_translator

# 直接使用 chromadb 而不是 vector_store（避免 embedding 模型加载问题）
from chromadb.config import Settings
import chromadb
from app.models import DocumentType

# 使用项目根目录的 data/chroma_db
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

question = "内存值为0时，支付4内存，在我方五级紫色数码兽上进化BT20-073，对面场上有BT23-058，该怎么处理效果？"

print("=" * 60)
print("完整查询流程测试")
print("=" * 60)

# 1. 提取卡牌编号
print("\n[步骤1] 提取卡牌编号")
card_numbers = query_processor.extract_card_numbers(question)
print(f"提取到: {card_numbers}")

# 2. 搜索卡牌
print("\n[步骤2] 搜索卡牌")
client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)

all_docs = []
collection = client.get_collection("card_game_rule")
docs_data = collection.get(include=["documents", "metadatas"])

for card_no in card_numbers:
    card_no_upper = card_no.upper()
    print(f"\n搜索: {card_no_upper}")
    
    for i, doc in enumerate(docs_data["documents"]):
        if f"【{card_no_upper}】" in doc:
            translated = terminology_translator.translate_result_to_chinese(doc)
            all_docs.append({
                "content": translated,
                "metadata": docs_data["metadatas"][i],
                "doc_type": "rule"
            })
            print(f"  找到! 标题: {docs_data['metadatas'][i].get('title', 'N/A')}")
            break  # 每张卡只取一条

# 3. 构建上下文
print("\n[步骤3] 构建上下文")
context_parts = []
for i, doc in enumerate(all_docs, 1):
    title = doc['metadata'].get('title', '未知来源')
    context_parts.append(
        f"【参考{i}】\n"
        f"来源：{title}\n"
        f"内容：{doc['content']}\n"
    )

context = "\n\n".join(context_parts)
print(f"上下文长度: {len(context)} 字符")
print(f"参考文档数: {len(all_docs)}")

# 4. 显示上下文内容
print("\n[步骤4] 上下文内容预览")
print("=" * 60)
for i, doc in enumerate(all_docs, 1):
    print(f"\n【参考{i}】")
    print(f"来源: {doc['metadata'].get('title', 'N/A')}")
    print(f"内容:\n{doc['content'][:500]}...")
    print("-" * 40)
