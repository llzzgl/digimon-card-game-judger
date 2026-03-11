"""调试搜索功能"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.rag import RAGManager, create_embedding_provider, SearchMode
from app.rag.types import DocumentType

print("=" * 80)
print("调试搜索功能")
print("=" * 80)

# 初始化RAG
rag = RAGManager(
    persist_dir="data/rag_store",
    embedding_provider=create_embedding_provider("local")
)

# 测试查询
query = "介绍一下数码兽攻击的流程"
print(f"\n查询: {query}")
print("=" * 80)

# 1. 测试向量搜索
print("\n1. 测试向量搜索")
print("-" * 80)
try:
    results = rag.search(
        query=query,
        doc_types=[DocumentType.RULE],
        mode=SearchMode.VECTOR,
        top_k=5
    )
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results[:3], 1):
        print(f"{i}. {r.metadata.title} (分数: {r.score:.3f})")
        print(f"   内容: {r.content[:100]}...")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试关键词搜索
print("\n2. 测试关键词搜索")
print("-" * 80)
try:
    results = rag.search(
        query=query,
        doc_types=[DocumentType.RULE],
        mode=SearchMode.KEYWORD,
        top_k=5
    )
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results[:3], 1):
        print(f"{i}. {r.metadata.title} (分数: {r.score:.3f})")
except Exception as e:
    print(f"❌ 错误: {e}")

# 3. 测试混合搜索（降低阈值）
print("\n3. 测试混合搜索（降低阈值）")
print("-" * 80)
try:
    # 临时修改配置
    rag.search_config.min_score = 0.0  # 移除分数过滤
    
    results = rag.search(
        query=query,
        doc_types=[DocumentType.RULE],
        mode=SearchMode.HYBRID,
        top_k=10
    )
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.metadata.title} (分数: {r.score:.3f})")
        print(f"   内容: {r.content[:100]}...")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 4. 直接查询ChromaDB
print("\n4. 直接查询ChromaDB")
print("-" * 80)
try:
    collection = rag.client.get_collection("dtcg_rule")
    print(f"集合中文档数: {collection.count()}")
    
    # 获取一些示例文档
    sample = collection.get(limit=3)
    print(f"\n示例文档:")
    for i, (doc_id, doc, meta) in enumerate(zip(sample['ids'], sample['documents'], sample['metadatas']), 1):
        print(f"{i}. {meta.get('title', 'N/A')}")
        print(f"   内容: {doc[:100]}...")
    
    # 直接查询
    print(f"\n直接查询: {query}")
    query_results = collection.query(
        query_texts=[query],
        n_results=5
    )
    
    if query_results['ids'] and query_results['ids'][0]:
        print(f"找到 {len(query_results['ids'][0])} 条结果")
        for i, (doc_id, distance, doc, meta) in enumerate(zip(
            query_results['ids'][0],
            query_results['distances'][0],
            query_results['documents'][0],
            query_results['metadatas'][0]
        ), 1):
            similarity = 1.0 - distance
            print(f"{i}. {meta.get('title', 'N/A')} (相似度: {similarity:.3f})")
            print(f"   内容: {doc[:100]}...")
    else:
        print("未找到结果")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试不同的查询
print("\n5. 测试不同的查询")
print("-" * 80)
test_queries = [
    "攻击",
    "アタック",
    "attack",
    "战斗",
    "数码兽攻击",
]

for q in test_queries:
    try:
        rag.search_config.min_score = 0.0
        results = rag.search(
            query=q,
            doc_types=[DocumentType.RULE],
            mode=SearchMode.HYBRID,
            top_k=3
        )
        print(f"\n查询 '{q}': {len(results)} 条结果")
        if results:
            print(f"  最佳匹配: {results[0].metadata.title} (分数: {results[0].score:.3f})")
    except Exception as e:
        print(f"查询 '{q}': 错误 - {e}")

print("\n" + "=" * 80)
print("调试完成")
print("=" * 80)
