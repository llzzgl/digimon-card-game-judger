"""检查向量数据库中的卡牌"""
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

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

print(f"向量库路径: {CHROMA_DIR}")
print(f"路径存在: {os.path.exists(CHROMA_DIR)}")

# 直接用 chromadb 查询
client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)

# 列出所有 collection
collections = client.list_collections()
print(f"\n现有 collections: {[c.name for c in collections]}")

for col in collections:
    print(f"\n=== {col.name} ===")
    print(f"文档数量: {col.count()}")
    
    # 尝试搜索 BT20-079
    results = col.get(
        where={"$contains": "BT20-079"},
        limit=5
    )
    if results and results['ids']:
        print(f"找到 BT20-079 相关文档: {len(results['ids'])} 条")
        for i, doc in enumerate(results['documents'][:2]):
            print(f"  文档 {i+1}: {doc[:150]}...")
