"""测试术语翻译和向量检索"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, '.')

from app.terminology_translator import terminology_translator
from app.vector_store import vector_store
from app.models import DocumentType

print("=" * 60)
print("术语翻译测试")
print("=" * 60)

# 测试翻译功能
test_terms = [
    "战斗暴龙兽",
    "亚古兽", 
    "阻挡者",
    "安防",
    "进化",
    "数码宝贝",
]

print("\n中文 → 日文 翻译测试:")
for term in test_terms:
    ja_query, translations = terminology_translator.translate_query_to_japanese(term)
    if translations:
        print(f"  {term} → {ja_query}")
    else:
        print(f"  {term} → (无匹配)")

print("\n" + "=" * 60)
print("向量检索测试（带翻译）")
print("=" * 60)

# 测试中文查询
test_queries = [
    "战斗暴龙兽的效果是什么",
    "阻挡者效果怎么用",
    "亚古兽可以进化成什么",
    "安防攻击+1是什么意思",
]

for query in test_queries:
    print(f"\n查询: {query}")
    print("-" * 40)
    
    results = vector_store.search(query, top_k=2)
    
    if not results:
        print("  无结果")
        continue
    
    for i, r in enumerate(results):
        title = r['metadata'].get('title', 'N/A')
        score = r['score']
        content = r['content'][:200].replace('\n', ' ')
        print(f"  [{i+1}] 标题: {title}")
        print(f"      分数: {score:.4f}")
        print(f"      内容(已翻译): {content}...")
        print()
