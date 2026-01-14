"""测试向量检索"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, '.')

from app.vector_store import vector_store
from app.models import DocumentType

# 测试几个查询
test_queries = [
    "ウォーグレイモン",  # 战斗暴龙兽
    "アグモン",  # 亚古兽
    "セキュリティ",  # 安防
    "ブロッカー",  # 阻挡者
    "进化费用",
    "数码宝贝名称",
]

print("=" * 60)
print("向量检索测试")
print("=" * 60)

for query in test_queries:
    print(f"\n查询: {query}")
    print("-" * 40)
    
    results = vector_store.search(query, top_k=3)
    
    if not results:
        print("  无结果")
        continue
    
    for i, r in enumerate(results):
        title = r['metadata'].get('title', 'N/A')
        score = r['score']
        content = r['content'][:150].replace('\n', ' ')
        print(f"  [{i+1}] 标题: {title}")
        print(f"      分数: {score:.4f}")
        print(f"      内容: {content}...")
        print()
