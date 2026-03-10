"""
RAG 系统安装测试脚本

用于验证 RAG 系统是否正确安装和配置
"""
import sys
from pathlib import Path

print("=" * 60)
print("RAG 系统安装测试")
print("=" * 60)

# 测试 1: 检查依赖
print("\n[1/5] 检查依赖包...")
dependencies = {
    'chromadb': 'ChromaDB 向量数据库',
    'sentence_transformers': 'Sentence Transformers 嵌入模型',
    'rank_bm25': 'BM25 搜索算法',
    'numpy': 'NumPy 数值计算'
}

missing_deps = []
for dep, desc in dependencies.items():
    try:
        __import__(dep)
        print(f"  ✅ {dep}: {desc}")
    except ImportError:
        print(f"  ❌ {dep}: {desc} - 未安装")
        missing_deps.append(dep)

if missing_deps:
    print(f"\n❌ 缺少依赖: {', '.join(missing_deps)}")
    print("请运行: pip install -r requirements_rag.txt")
    sys.exit(1)

# 测试 2: 导入 RAG 模块
print("\n[2/5] 导入 RAG 模块...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from app.rag import (
        RAGManager,
        DocumentType,
        DocumentSource,
        DocumentMetadata,
        SearchMode,
        create_embedding_provider
    )
    print("  ✅ 所有模块导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    sys.exit(1)

# 测试 3: 初始化 RAG 管理器
print("\n[3/5] 初始化 RAG 管理器...")
try:
    test_dir = Path(__file__).parent / "data" / "test_rag_store"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    rag = RAGManager(
        persist_dir=str(test_dir),
        embedding_provider=create_embedding_provider("local")
    )
    print("  ✅ RAG 管理器初始化成功")
    print(f"  📁 数据目录: {test_dir}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 添加测试文档
print("\n[4/5] 添加测试文档...")
try:
    from datetime import datetime
    
    test_content = """
    【测试规则】
    这是一个测试文档，用于验证 RAG 系统是否正常工作。
    
    1. 文档分块功能
    2. 嵌入生成功能
    3. 向量存储功能
    """
    
    metadata = DocumentMetadata(
        doc_id="test_001",
        title="测试文档",
        doc_type=DocumentType.RULE,
        source=DocumentSource.USER,
        created_at=datetime.now()
    )
    
    result = rag.add_document(test_content, metadata)
    print(f"  ✅ 文档添加成功")
    print(f"  📄 文档 ID: {result['doc_id']}")
    print(f"  📊 分块数: {result['chunk_count']}")
except Exception as e:
    print(f"  ❌ 添加文档失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 5: 搜索测试
print("\n[5/5] 测试搜索功能...")
try:
    query = "测试"
    results = rag.search(query, top_k=3)
    
    print(f"  ✅ 搜索成功")
    print(f"  🔍 查询: {query}")
    print(f"  📊 结果数: {len(results)}")
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n  结果 {i}:")
            print(f"    标题: {result.metadata.title}")
            print(f"    类型: {result.doc_type.value}")
            print(f"    分数: {result.score:.3f}")
            print(f"    内容: {result.content[:50]}...")
except Exception as e:
    print(f"  ❌ 搜索失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 6: Prompt 构建
print("\n[6/6] 测试 Prompt 构建...")
try:
    prompt = rag.build_prompt(query, results)
    print(f"  ✅ Prompt 构建成功")
    print(f"  📝 Prompt 长度: {len(prompt)} 字符")
    print(f"\n  Prompt 预览:")
    print("  " + "-" * 56)
    preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
    for line in preview.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 56)
except Exception as e:
    print(f"  ❌ Prompt 构建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 清理测试数据
print("\n[清理] 删除测试数据...")
try:
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("  ✅ 测试数据已清理")
except Exception as e:
    print(f"  ⚠️  清理失败: {e}")

# 总结
print("\n" + "=" * 60)
print("✅ 所有测试通过！RAG 系统安装成功")
print("=" * 60)
print("\n下一步:")
print("  1. 运行示例: python example_new_rag.py")
print("  2. 迁移数据: python migrate_to_new_rag.py")
print("  3. 阅读文档: app/rag/README.md")
print("\n" + "=" * 60)
