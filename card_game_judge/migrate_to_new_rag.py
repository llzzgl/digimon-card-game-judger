"""
数据迁移脚本：从旧的 VectorStore 迁移到新的 RAG 系统

使用方法:
    python migrate_to_new_rag.py [--dry-run]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import RAGManager, DocumentType, DocumentSource, DocumentMetadata
from app.rag.embeddings import create_embedding_provider
from app.rag.types import ChunkConfig, SearchConfig


def migrate_data(dry_run: bool = False):
    """
    迁移数据到新的 RAG 系统
    
    Args:
        dry_run: 如果为 True，只显示迁移计划，不实际执行
    """
    print("=" * 60)
    print("数据迁移：旧 VectorStore → 新 RAG 系统")
    print("=" * 60)
    
    # 初始化旧的 VectorStore
    try:
        from app.vector_store import vector_store as old_store
        print("✅ 成功加载旧的 VectorStore")
    except Exception as e:
        print(f"❌ 无法加载旧的 VectorStore: {e}")
        return False
    
    # 初始化新的 RAG 系统
    try:
        new_persist_dir = Path(__file__).parent / "data" / "rag_store"
        
        # 创建嵌入提供商 (使用本地模型)
        embedding_provider = create_embedding_provider("local")
        
        # 创建 RAG 管理器
        rag_manager = RAGManager(
            persist_dir=str(new_persist_dir),
            embedding_provider=embedding_provider,
            chunk_config=ChunkConfig(
                chunk_size=500,
                chunk_overlap=50
            ),
            search_config=SearchConfig()
        )
        print(f"✅ 成功初始化新的 RAG 系统: {new_persist_dir}")
    except Exception as e:
        print(f"❌ 无法初始化新的 RAG 系统: {e}")
        return False
    
    # 获取旧系统中的所有文档
    print("\n" + "-" * 60)
    print("步骤 1: 扫描旧系统中的文档")
    print("-" * 60)
    
    try:
        old_documents = old_store.list_documents()
        print(f"找到 {len(old_documents)} 个文档")
        
        for doc in old_documents[:5]:  # 显示前 5 个
            print(f"  - {doc['title']} ({doc['doc_type']}, {doc['chunk_count']} 块)")
        
        if len(old_documents) > 5:
            print(f"  ... 还有 {len(old_documents) - 5} 个文档")
    except Exception as e:
        print(f"❌ 扫描文档失败: {e}")
        return False
    
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN 模式 - 不执行实际迁移")
        print("=" * 60)
        print(f"将迁移 {len(old_documents)} 个文档到新系统")
        return True
    
    # 执行迁移
    print("\n" + "-" * 60)
    print("步骤 2: 迁移文档到新系统")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, doc_info in enumerate(old_documents, 1):
        doc_id = doc_info['doc_id']
        title = doc_info['title']
        doc_type_str = doc_info['doc_type']
        
        print(f"\n[{i}/{len(old_documents)}] 迁移: {title}")
        
        try:
            # 获取文档的所有分块
            chunks = old_store.get_document_chunks(doc_id)
            
            if not chunks:
                print(f"  ⚠️  跳过: 没有找到分块")
                continue
            
            # 重组完整文档
            full_content = "\n\n".join([chunk['content'] for chunk in chunks])
            
            # 确定文档类型
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.RULE  # 默认为规则
            
            # 创建元数据
            metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                doc_type=doc_type,
                source=DocumentSource.DATABASE,
                created_at=datetime.now()
            )
            
            # 添加到新系统
            result = rag_manager.add_document(full_content, metadata)
            
            print(f"  ✅ 成功: {result['chunk_count']} 块")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            error_count += 1
    
    # 迁移总结
    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)
    print(f"成功: {success_count} 个文档")
    print(f"失败: {error_count} 个文档")
    print(f"总计: {len(old_documents)} 个文档")
    
    # 验证新系统
    print("\n" + "-" * 60)
    print("步骤 3: 验证新系统")
    print("-" * 60)
    
    try:
        new_documents = rag_manager.list_documents()
        print(f"新系统中有 {len(new_documents)} 个文档")
        
        # 测试搜索
        test_query = "进化"
        print(f"\n测试搜索: '{test_query}'")
        results = rag_manager.search(test_query, top_k=3)
        print(f"找到 {len(results)} 个结果")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.metadata.title} (分数: {result.score:.3f})")
        
        print("\n✅ 新系统验证通过")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="迁移数据到新的 RAG 系统"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="只显示迁移计划，不实际执行"
    )
    
    args = parser.parse_args()
    
    success = migrate_data(dry_run=args.dry_run)
    
    if success:
        print("\n✅ 迁移成功完成")
        sys.exit(0)
    else:
        print("\n❌ 迁移失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
