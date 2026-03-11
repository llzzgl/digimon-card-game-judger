"""
数据导入脚本 - 将数据导入到新 RAG 系统

支持导入：
1. 规则文档（PDF、TXT、JSON）
2. 官方裁定（JSON）
3. 卡牌数据（JSON）

使用方法：
    # 导入规则文档
    python import_data.py --type rule --file "规则书/综合规则.pdf" --title "综合规则 v1.0"
    
    # 批量导入目录
    python import_data.py --type ruling --dir "官方QA" --pattern "*.json"
    
    # 导入卡牌数据（自动从 digimon_card_data_chiness 加载）
    python import_data.py --import-cards
    
    # 列出所有文档
    python import_data.py --list
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import (
    RAGManager,
    DocumentType,
    DocumentSource,
    DocumentMetadata,
    create_embedding_provider
)


class DataImporter:
    """数据导入器"""
    
    def __init__(self, rag_dir: str = "data/rag_store"):
        """初始化导入器"""
        print("🚀 初始化数据导入器...")
        self.rag = RAGManager(
            persist_dir=rag_dir,
            embedding_provider=create_embedding_provider("local")
        )
        print("✅ 初始化完成\n")
    
    def import_file(
        self,
        file_path: str,
        doc_type: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        导入单个文件
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型 (rule/ruling/card)
            title: 文档标题（可选，默认使用文件名）
            tags: 标签列表
        
        Returns:
            是否成功
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        # 确定文档类型
        try:
            dtype = DocumentType(doc_type)
        except ValueError:
            print(f"❌ 无效的文档类型: {doc_type}")
            print("   可选: rule, ruling, card")
            return False
        
        # 确定标题
        if not title:
            title = file_path.stem
        
        # 读取文件内容
        try:
            content = self._read_file(file_path)
            if not content:
                print(f"❌ 文件内容为空: {file_path}")
                return False
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return False
        
        # 创建元数据
        metadata = DocumentMetadata(
            doc_id=f"{doc_type}_{file_path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=title,
            doc_type=dtype,
            source=DocumentSource.DATABASE,
            tags=tags or [],
            created_at=datetime.now()
        )
        
        # 导入到 RAG 系统
        try:
            result = self.rag.add_document(content, metadata)
            print(f"✅ 导入成功: {title}")
            print(f"   文档 ID: {result['doc_id']}")
            print(f"   分块数: {result['chunk_count']}")
            return True
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False
    
    def import_directory(
        self,
        dir_path: str,
        doc_type: str,
        pattern: str = "*.json",
        tags: Optional[List[str]] = None
    ) -> dict:
        """
        批量导入目录中的文件
        
        Args:
            dir_path: 目录路径
            doc_type: 文档类型
            pattern: 文件匹配模式
            tags: 标签列表
        
        Returns:
            导入统计 {success: int, failed: int}
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            print(f"❌ 目录不存在: {dir_path}")
            return {"success": 0, "failed": 0}
        
        files = list(dir_path.glob(pattern))
        if not files:
            print(f"❌ 未找到匹配 {pattern} 的文件")
            return {"success": 0, "failed": 0}
        
        print(f"📁 找到 {len(files)} 个文件")
        print()
        
        success = 0
        failed = 0
        
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {file_path.name}")
            if self.import_file(str(file_path), doc_type, tags=tags):
                success += 1
            else:
                failed += 1
            print()
        
        print("=" * 60)
        print(f"导入完成: 成功 {success}, 失败 {failed}")
        print("=" * 60)
        
        return {"success": success, "failed": failed}
    
    def import_cards(self, cards_file: Optional[str] = None) -> bool:
        """
        导入卡牌数据
        
        Args:
            cards_file: 卡牌数据文件路径（可选）
        
        Returns:
            是否成功
        """
        # 默认使用中文卡牌数据
        if not cards_file:
            cards_file = Path(__file__).parent.parent / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        else:
            cards_file = Path(cards_file)
        
        if not cards_file.exists():
            print(f"❌ 卡牌数据文件不存在: {cards_file}")
            return False
        
        print(f"📦 导入卡牌数据: {cards_file}")
        
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            
            print(f"   找到 {len(cards)} 张卡牌")
            
            success = 0
            failed = 0
            
            for i, card in enumerate(cards, 1):
                card_no = card.get('card_no', '')
                name_cn = card.get('name_cn', '')
                
                if not card_no:
                    failed += 1
                    continue
                
                # 格式化卡牌内容
                content = self._format_card(card)
                
                # 创建元数据
                metadata = DocumentMetadata(
                    doc_id=f"card_{card_no}",
                    title=f"{card_no} {name_cn}",
                    doc_type=DocumentType.CARD,
                    source=DocumentSource.DATABASE,
                    card_no=card_no,
                    tags=["卡牌数据"],
                    created_at=datetime.now()
                )
                
                try:
                    self.rag.add_document(content, metadata)
                    success += 1
                    
                    if i % 100 == 0:
                        print(f"   进度: {i}/{len(cards)}")
                
                except Exception as e:
                    print(f"   ❌ 导入失败 {card_no}: {e}")
                    failed += 1
            
            print()
            print("=" * 60)
            print(f"卡牌导入完成: 成功 {success}, 失败 {failed}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ 导入卡牌数据失败: {e}")
            return False
    
    def list_documents(self, doc_type: Optional[str] = None):
        """
        列出所有文档
        
        Args:
            doc_type: 文档类型过滤（可选）
        """
        dtype = None
        if doc_type:
            try:
                dtype = DocumentType(doc_type)
            except ValueError:
                print(f"❌ 无效的文档类型: {doc_type}")
                return
        
        documents = self.rag.list_documents(dtype)
        
        if not documents:
            print("📭 没有找到文档")
            return
        
        # 按类型分组
        by_type = {}
        for doc in documents:
            doc_type = doc['doc_type']
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)
        
        print("\n" + "=" * 60)
        print("文档列表")
        print("=" * 60)
        
        for doc_type, docs in by_type.items():
            type_label = {"rule": "规则", "ruling": "裁定", "card": "卡牌"}.get(doc_type, doc_type)
            print(f"\n【{type_label}】({len(docs)} 个文档)")
            print("-" * 60)
            
            for doc in docs[:10]:  # 每种类型最多显示 10 个
                print(f"  - {doc['title']}")
                print(f"    ID: {doc['doc_id']}, 分块数: {doc['chunk_count']}")
            
            if len(docs) > 10:
                print(f"  ... 还有 {len(docs) - 10} 个文档")
        
        print("\n" + "=" * 60)
        print(f"总计: {len(documents)} 个文档")
        print("=" * 60)
    
    def _read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        ext = file_path.suffix.lower()
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 如果是 QA 格式
                if isinstance(data, list):
                    parts = []
                    for item in data:
                        if 'question' in item and 'answer' in item:
                            parts.append(f"Q: {item['question']}\nA: {item['answer']}")
                        else:
                            parts.append(json.dumps(item, ensure_ascii=False))
                    return "\n\n".join(parts)
                else:
                    return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.pdf':
            # 需要 PDF 处理库
            try:
                from app.pdf_processor import extract_text_from_bytes
                content = file_path.read_bytes()
                return extract_text_from_bytes(content, file_path.name)
            except ImportError:
                print("⚠️  PDF 处理需要安装 pypdf 库")
                return ""
        
        else:
            # 尝试作为文本读取
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _format_card(self, card: dict) -> str:
        """格式化卡牌数据为文本"""
        parts = []
        
        if card.get('card_no'):
            parts.append(f"卡牌编号: {card['card_no']}")
        if card.get('name_cn'):
            parts.append(f"中文名: {card['name_cn']}")
        if card.get('name_jp'):
            parts.append(f"日文名: {card['name_jp']}")
        if card.get('type'):
            parts.append(f"类型: {card['type']}")
        if card.get('color'):
            parts.append(f"颜色: {card['color']}")
        if card.get('rarity'):
            parts.append(f"稀有度: {card['rarity']}")
        if card.get('level'):
            parts.append(f"等级: Lv.{card['level']}")
        if card.get('play_cost'):
            parts.append(f"登场费用: {card['play_cost']}")
        if card.get('dp') and card['dp'] != '-':
            parts.append(f"DP: {card['dp']}")
        if card.get('form'):
            parts.append(f"形态: {card['form']}")
        if card.get('attribute'):
            parts.append(f"属性: {card['attribute']}")
        if card.get('species'):
            parts.append(f"种族: {card['species']}")
        if card.get('evolution_condition'):
            parts.append(f"进化条件: {card['evolution_condition']}")
        if card.get('effect'):
            parts.append(f"效果: {card['effect']}")
        if card.get('inherited_effect'):
            parts.append(f"继承效果: {card['inherited_effect']}")
        if card.get('security_effect'):
            parts.append(f"安防效果: {card['security_effect']}")
        
        return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="数据导入脚本 - 新 RAG 系统")
    
    # 导入选项
    parser.add_argument("--type", type=str, choices=["rule", "ruling", "card"],
                        help="文档类型")
    parser.add_argument("--file", type=str, help="导入单个文件")
    parser.add_argument("--dir", type=str, help="批量导入目录")
    parser.add_argument("--pattern", type=str, default="*.json", help="文件匹配模式")
    parser.add_argument("--title", type=str, help="文档标题")
    parser.add_argument("--tags", type=str, help="标签，逗号分隔")
    
    # 特殊导入
    parser.add_argument("--import-cards", action="store_true", help="导入卡牌数据")
    parser.add_argument("--cards-file", type=str, help="卡牌数据文件路径")
    
    # 查询选项
    parser.add_argument("--list", action="store_true", help="列出所有文档")
    parser.add_argument("--list-type", type=str, help="列出指定类型的文档")
    
    # 配置
    parser.add_argument("--rag-dir", type=str, default="data/rag_store", help="RAG 数据目录")
    
    args = parser.parse_args()
    
    # 初始化导入器
    importer = DataImporter(rag_dir=args.rag_dir)
    
    # 执行操作
    if args.list or args.list_type:
        importer.list_documents(args.list_type)
    
    elif args.import_cards:
        importer.import_cards(args.cards_file)
    
    elif args.file and args.type:
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        importer.import_file(args.file, args.type, args.title, tags)
    
    elif args.dir and args.type:
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        importer.import_directory(args.dir, args.type, args.pattern, tags)
    
    else:
        parser.print_help()
        print("\n示例:")
        print("  # 导入规则文档")
        print('  python import_data.py --type rule --file "规则书/综合规则.pdf" --title "综合规则"')
        print("\n  # 批量导入裁定")
        print('  python import_data.py --type ruling --dir "官方QA" --pattern "*.json"')
        print("\n  # 导入卡牌数据")
        print("  python import_data.py --import-cards")
        print("\n  # 列出所有文档")
        print("  python import_data.py --list")


if __name__ == "__main__":
    main()
