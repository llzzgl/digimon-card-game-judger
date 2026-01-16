"""检查向量数据库中的卡牌 - 使用文本搜索"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, '.')

from chromadb.config import Settings
import chromadb

# 使用项目根目录的 data/chroma_db
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)

col = client.get_collection("card_game_rule")

# 获取所有文档并搜索
print("正在搜索 BT20-079 和 BT23-058...")
results = col.get(limit=10456, include=["documents", "metadatas"])

found_bt20 = []
found_bt23 = []

for i, doc in enumerate(results['documents']):
    if 'BT20-079' in doc:
        found_bt20.append((i, doc[:200], results['metadatas'][i]))
    if 'BT23-058' in doc:
        found_bt23.append((i, doc[:200], results['metadatas'][i]))

print(f"\n找到 BT20-079: {len(found_bt20)} 条")
for idx, doc, meta in found_bt20[:2]:
    print(f"  标题: {meta.get('title', 'N/A')}")
    print(f"  内容: {doc}...")
    print()

print(f"\n找到 BT23-058: {len(found_bt23)} 条")
for idx, doc, meta in found_bt23[:2]:
    print(f"  标题: {meta.get('title', 'N/A')}")
    print(f"  内容: {doc}...")
    print()
