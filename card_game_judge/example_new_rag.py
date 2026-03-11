"""
新 RAG 系统使用示例

展示如何使用新的 RAG 系统进行：
1. 文档索引
2. 智能检索
3. Prompt 构建
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import (
    RAGManager,
    DocumentType,
    DocumentSource,
    DocumentMetadata,
    SearchMode,
    create_embedding_provider
)
from datetime import datetime


def example_1_add_documents():
    """示例 1: 添加文档到 RAG 系统"""
    print("=" * 60)
    print("示例 1: 添加文档")
    print("=" * 60)
    
    # 初始化 RAG 管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 添加规则文档
    rule_content = """
    【进化规则】
    
    1. 进化条件
    玩家可以将手牌中的数码宝贝卡放置在场上已有的数码宝贝上方进行进化。
    进化时需要支付进化费用，并满足进化条件（颜色、等级等）。
    
    2. 进化效果
    进化时，新卡牌的效果会立即生效。
    进化后的数码宝贝会继承下方所有卡牌的【继承效果】。
    
    3. 进化时机
    进化只能在自己的主要阶段进行。
    每回合可以进化多次，但同一只数码宝贝每回合只能进化一次。
    """
    
    rule_metadata = DocumentMetadata(
        doc_id="rule_evolution_001",
        title="进化规则详解",
        doc_type=DocumentType.RULE,
        source=DocumentSource.OFFICIAL,
        version="v1.0",
        tags=["进化", "基础规则"]
    )
    
    result = rag.add_document(rule_content, rule_metadata)
    print(f"✅ 添加规则文档: {result['title']}")
    print(f"   分块数: {result['chunk_count']}")
    
    # 添加裁定文档
    ruling_content = """
    Q: 如果我的数码宝贝在进化时被对手的效果破坏，进化费用会退还吗？
    A: 不会。进化费用在宣告进化时就已经支付，即使进化被中断，费用也不会退还。
    
    Q: 进化后的数码宝贝会继承下方所有卡牌的继承效果吗？
    A: 是的。进化后的数码宝贝会同时拥有所有下方卡牌的继承效果。
    """
    
    ruling_metadata = DocumentMetadata(
        doc_id="ruling_evolution_001",
        title="进化相关裁定",
        doc_type=DocumentType.RULING,
        source=DocumentSource.OFFICIAL,
        tags=["进化", "QA"]
    )
    
    result = rag.add_document(ruling_content, ruling_metadata)
    print(f"✅ 添加裁定文档: {result['title']}")
    print(f"   分块数: {result['chunk_count']}")


def example_2_search():
    """示例 2: 搜索文档"""
    print("\n" + "=" * 60)
    print("示例 2: 搜索文档")
    print("=" * 60)
    
    # 初始化 RAG 管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 搜索 1: 向量搜索
    print("\n【向量搜索】")
    query = "进化时费用会退还吗"
    results = rag.search(
        query=query,
        mode=SearchMode.VECTOR,
        top_k=3
    )
    
    print(f"查询: {query}")
    print(f"找到 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata.title}")
        print(f"   类型: {result.doc_type.value}")
        print(f"   分数: {result.score:.3f}")
        print(f"   内容: {result.content[:100]}...")
        print()
    
    # 搜索 2: 混合搜索
    print("\n【混合搜索】")
    query = "继承效果"
    results = rag.search(
        query=query,
        mode=SearchMode.HYBRID,
        top_k=3
    )
    
    print(f"查询: {query}")
    print(f"找到 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata.title}")
        print(f"   类型: {result.doc_type.value}")
        print(f"   分数: {result.score:.3f}")
        print()
    
    # 搜索 3: 限定文档类型
    print("\n【限定搜索 - 仅裁定】")
    query = "进化"
    results = rag.search(
        query=query,
        doc_types=[DocumentType.RULING],
        top_k=3
    )
    
    print(f"查询: {query}")
    print(f"找到 {len(results)} 个结果 (仅裁定):\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata.title}")
        print(f"   类型: {result.doc_type.value}")
        print()


def example_3_build_prompt():
    """示例 3: 构建结构化 Prompt"""
    print("\n" + "=" * 60)
    print("示例 3: 构建结构化 Prompt")
    print("=" * 60)
    
    # 初始化 RAG 管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 用户问题
    query = "进化时如果被破坏，费用会退还吗？"
    
    # 搜索相关文档
    results = rag.search(query, top_k=5)
    
    # 搜索相关卡牌 (假设问题中提到了卡号)
    card_data = None
    # card_data = [rag.search_card_by_number("BT1-001")]
    
    # 构建 Prompt
    prompt = rag.build_prompt(query, results, card_data)
    
    print("\n【生成的 Prompt】")
    print("-" * 60)
    print(prompt)
    print("-" * 60)


def example_4_card_search():
    """示例 4: 卡牌精确搜索"""
    print("\n" + "=" * 60)
    print("示例 4: 卡牌精确搜索")
    print("=" * 60)
    
    # 初始化 RAG 管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 搜索卡牌
    card_numbers = ["BT1-001", "BT1-020", "ST1-01"]
    
    for card_no in card_numbers:
        print(f"\n搜索卡牌: {card_no}")
        card = rag.search_card_by_number(card_no)
        
        if card:
            print(f"✅ 找到: {card.get('name_cn', 'N/A')}")
            print(f"   类型: {card.get('type', 'N/A')}")
            print(f"   颜色: {card.get('color', 'N/A')}")
            if card.get('effect'):
                print(f"   效果: {card['effect'][:50]}...")
        else:
            print(f"❌ 未找到")


def example_5_list_documents():
    """示例 5: 列出所有文档"""
    print("\n" + "=" * 60)
    print("示例 5: 列出所有文档")
    print("=" * 60)
    
    # 初始化 RAG 管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 列出所有文档
    documents = rag.list_documents()
    
    print(f"\n共有 {len(documents)} 个文档:\n")
    
    for doc in documents:
        print(f"- {doc['title']}")
        print(f"  ID: {doc['doc_id']}")
        print(f"  类型: {doc['doc_type']}")
        print(f"  分块数: {doc['chunk_count']}")
        print()


def main():
    """运行所有示例"""
    print("新 RAG 系统使用示例\n")
    
    try:
        # 示例 1: 添加文档
        example_1_add_documents()
        
        # 示例 2: 搜索文档
        example_2_search()
        
        # 示例 3: 构建 Prompt
        example_3_build_prompt()
        
        # 示例 4: 卡牌搜索
        example_4_card_search()
        
        # 示例 5: 列出文档
        example_5_list_documents()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
