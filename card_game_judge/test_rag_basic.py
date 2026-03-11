"""
RAG 系统基础测试（不需要下载模型）

测试模块导入和基本功能
"""
import sys
from pathlib import Path

print("=" * 60)
print("RAG 系统基础测试（快速版）")
print("=" * 60)

# 测试 1: 检查依赖
print("\n[1/4] 检查依赖包...")
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
print("\n[2/4] 导入 RAG 模块...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from app.rag import (
        DocumentType,
        DocumentSource,
        DocumentMetadata,
        SearchMode,
        SearchConfig,
        ChunkConfig
    )
    print("  ✅ 类型模块导入成功")
    
    from app.rag import DocumentChunker
    print("  ✅ 分块器导入成功")
    
    from app.rag import PromptBuilder
    print("  ✅ Prompt 构建器导入成功")
    
    from app.rag import HybridSearchEngine
    print("  ✅ 搜索引擎导入成功")
    
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 测试分块器
print("\n[3/4] 测试文档分块器...")
try:
    chunker = DocumentChunker(ChunkConfig(
        chunk_size=100,
        chunk_overlap=20
    ))
    
    test_text = """
    这是一个测试文档。
    
    第一段内容：介绍数码宝贝卡牌游戏的基本规则。
    
    第二段内容：说明进化的条件和流程。
    
    第三段内容：解释战斗阶段的详细步骤。
    """
    
    chunks = chunker.chunk_text(test_text, DocumentType.RULE)
    print(f"  ✅ 分块成功")
    print(f"  📊 原文长度: {len(test_text)} 字符")
    print(f"  📊 分块数量: {len(chunks)} 块")
    
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n  块 {i} ({len(chunk)} 字符):")
        preview = chunk[:50].replace('\n', ' ')
        print(f"    {preview}...")
    
except Exception as e:
    print(f"  ❌ 分块测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 测试 Prompt 构建器
print("\n[4/4] 测试 Prompt 构建器...")
try:
    from app.rag import SearchResult
    from datetime import datetime
    
    builder = PromptBuilder()
    
    # 创建模拟搜索结果
    mock_results = [
        SearchResult(
            content="进化时需要支付进化费用，并满足进化条件。",
            metadata=DocumentMetadata(
                doc_id="rule_001",
                title="进化规则",
                doc_type=DocumentType.RULE,
                source=DocumentSource.DATABASE,
                version="v1.0",
                created_at=datetime.now()
            ),
            score=0.95,
            doc_type=DocumentType.RULE
        ),
        SearchResult(
            content="Q: 进化费用会退还吗？ A: 不会，费用已经支付。",
            metadata=DocumentMetadata(
                doc_id="qa_001",
                title="进化相关 QA",
                doc_type=DocumentType.RULING,
                source=DocumentSource.DATABASE,
                created_at=datetime.now()
            ),
            score=0.88,
            doc_type=DocumentType.RULING
        )
    ]
    
    query = "进化时如果被破坏，费用会退还吗？"
    prompt = builder.build(query, mock_results)
    
    print(f"  ✅ Prompt 构建成功")
    print(f"  📝 Prompt 长度: {len(prompt)} 字符")
    print(f"\n  Prompt 预览:")
    print("  " + "-" * 56)
    
    lines = prompt.split('\n')[:15]
    for line in lines:
        print(f"  {line}")
    
    if len(prompt.split('\n')) > 15:
        print("  ...")
    
    print("  " + "-" * 56)
    
except Exception as e:
    print(f"  ❌ Prompt 构建测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 总结
print("\n" + "=" * 60)
print("✅ 基础测试全部通过！")
print("=" * 60)
print("\n模块功能正常，可以继续进行完整测试。")
print("\n下一步:")
print("  1. 运行完整测试（会下载模型）:")
print("     D:\\python\\Anaconda\\envs\\LLMs\\python.exe test_rag_installation.py")
print("\n  2. 或直接运行示例:")
print("     D:\\python\\Anaconda\\envs\\LLMs\\python.exe example_new_rag.py")
print("\n  3. 查看首次运行说明:")
print("     首次运行说明.md")
print("\n" + "=" * 60)
