"""测试RAG检索功能"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.rag import RAGManager, create_embedding_provider, SearchMode
from app.rag.types import DocumentType

print("=" * 80)
print("测试RAG检索功能")
print("=" * 80)

# 初始化RAG管理器
print("\n初始化RAG管理器...")
rag = RAGManager(
    persist_dir="data/rag_store",
    embedding_provider=create_embedding_provider("local")
)

# 检查各类型文档数量
print("\n" + "=" * 80)
print("检查文档数量")
print("=" * 80)

for doc_type in DocumentType:
    try:
        collection_name = f"dtcg_{doc_type.value}"
        collection = rag.client.get_collection(collection_name)
        count = collection.count()
        print(f"{doc_type.value:10s}: {count:5d} 条")
    except Exception as e:
        print(f"{doc_type.value:10s}: 0 条 (集合不存在)")

# 测试检索
print("\n" + "=" * 80)
print("测试检索")
print("=" * 80)

test_queries = [
    "介绍一下数码兽攻击的流程",
    "攻击流程",
    "アタック",
    "attack",
    "进化时费用会退还吗",
]

for query in test_queries:
    print(f"\n查询: {query}")
    print("-" * 80)
    
    # 检索规则和裁定
    results = rag.search(
        query=query,
        doc_types=[DocumentType.RULE, DocumentType.RULING, DocumentType.CASE],
        mode=SearchMode.HYBRID,
        top_k=3
    )
    
    if results:
        print(f"找到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.metadata.title}")
            print(f"   类型: {result.doc_type.value}")
            print(f"   分数: {result.score:.3f}")
            print(f"   内容预览: {result.content[:100]}...")
    else:
        print("❌ 未找到任何结果")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

# 检查是否需要导入数据
print("\n💡 如果所有文档数量都是0，说明需要导入数据")
print("   请运行: python import_data.py")
