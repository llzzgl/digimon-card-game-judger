"""
重建向量数据库 - 使用新的多语言 embedding 模型
运行前会清空现有数据！

用法:
  python rebuild_vectordb.py                    # 重建全部数据
  python rebuild_vectordb.py --import-rules     # 导入规则书（弹出文件选择框）
  python rebuild_vectordb.py --import-rules path/to/file.pdf  # 导入指定规则书
"""
import os
import shutil
import time
import argparse

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

from tqdm import tqdm
from pathlib import Path


def import_rule_files(file_paths=None):
    """
    导入规则书文件
    
    Args:
        file_paths: 文件路径列表，如果为 None 则弹出文件选择框
    """
    # 导入模块
    import sys
    sys.path.insert(0, '.')
    from app.vector_store import vector_store
    from app.pdf_processor import extract_text_from_bytes
    from app.models import DocumentType, DocumentMetadata
    
    # 如果没有指定文件，弹出文件选择框
    if not file_paths:
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)  # 置顶
            
            file_paths = filedialog.askopenfilenames(
                title="选择规则书文件（可多选）",
                filetypes=[
                    ("支持的文件", "*.pdf *.txt *.json"),
                    ("PDF 文件", "*.pdf"),
                    ("文本文件", "*.txt"),
                    ("JSON 文件", "*.json"),
                    ("所有文件", "*.*")
                ]
            )
            root.destroy()
            
            if not file_paths:
                print("未选择文件，退出")
                return
        except Exception as e:
            print(f"无法打开文件选择框: {e}")
            print("请使用命令行指定文件路径: python rebuild_vectordb.py --import-rules path/to/file.pdf")
            return
    
    # 确保是列表
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    print(f"\n准备导入 {len(file_paths)} 个规则书文件...")
    print("=" * 50)
    
    success = 0
    failed = 0
    total_chunks = 0
    
    for file_path in file_paths:
        p = Path(file_path)
        if not p.exists():
            print(f"  ✗ 文件不存在: {file_path}")
            failed += 1
            continue
        
        try:
            print(f"\n📄 处理: {p.name}")
            
            content = p.read_bytes()
            text = extract_text_from_bytes(content, p.name)
            
            if not text.strip():
                print(f"  ✗ 无法提取文本")
                failed += 1
                continue
            
            # 生成标题（去掉扩展名）
            title = p.stem
            
            metadata = DocumentMetadata(
                doc_type=DocumentType.RULE,
                title=title,
                source=str(p.absolute()),
                tags=['规则书', '官方规则']
            )
            
            result = vector_store.add_document(text, metadata)
            total_chunks += result['chunk_count']
            success += 1
            
            print(f"  ✓ 导入成功: {result['chunk_count']} chunks")
            
        except Exception as e:
            print(f"  ✗ 导入失败: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"规则书导入完成: 成功 {success}, 失败 {failed}, 总计 {total_chunks} chunks")


def rebuild_all():
    """重建全部向量数据库"""
    # 清空现有向量库
    CHROMA_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")
    if os.path.exists(CHROMA_DIR):
        print(f"清空现有向量库: {CHROMA_DIR}")
        try:
            shutil.rmtree(CHROMA_DIR)
        except PermissionError:
            print("文件被占用，尝试强制删除...")
            import gc
            gc.collect()
            time.sleep(1)
            for root, dirs, files in os.walk(CHROMA_DIR, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except:
                        pass
            try:
                os.rmdir(CHROMA_DIR)
            except:
                print("无法完全清空，将使用新目录")
                CHROMA_DIR = CHROMA_DIR + "_new"
        os.makedirs(CHROMA_DIR, exist_ok=True)
        print("已清空")

    print("\n开始重新导入数据...")
    print("=" * 50)

    # 导入模块
    import sys
    sys.path.insert(0, '.')
    from app.vector_store import vector_store
    from app.pdf_processor import extract_text_from_bytes
    from app.models import DocumentType, DocumentMetadata

    # 1. 导入术语对照表
    print("\n[1/3] 导入术语对照表...")
    terminology_files = [
        ('../digimon_data/dtcg_terminology.json', 'DTCG术语对照表'),
        ('../digimon_data/digimon_name_mapping.json', 'DTCG数码宝贝名称对照表')
    ]

    for file_path, title in tqdm(terminology_files, desc="术语对照表", unit="file"):
        p = Path(file_path)
        if not p.exists():
            continue
        content = p.read_bytes()
        text = extract_text_from_bytes(content, p.name)
        
        metadata = DocumentMetadata(
            doc_type=DocumentType.RULE,
            title=title,
            source=str(p),
            tags=['术语', '翻译', '日中对照']
        )
        
        result = vector_store.add_document(text, metadata)

    print("  术语对照表导入完成")

    # 2. 导入规则书 PDF
    print("\n[2/3] 导入规则书...")
    rule_files = [
        ('数码宝贝卡牌对战 综合规则 2025.12 日文版.pdf', '综合规则 2025.12 日文版'),
        ('数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf', '综合规则 1.2 中文版'),
        ('数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt', '综合规则 最新版 中文翻译'),
    ]

    for file_name, title in tqdm(rule_files, desc="规则书", unit="file"):
        p = Path(file_name)
        if not p.exists():
            continue
        
        try:
            content = p.read_bytes()
            text = extract_text_from_bytes(content, p.name)
            
            if not text.strip():
                continue
            
            metadata = DocumentMetadata(
                doc_type=DocumentType.RULE,
                title=title,
                source=str(p),
                tags=['规则书', '官方规则']
            )
            
            result = vector_store.add_document(text, metadata)
            tqdm.write(f"  ✓ {title}: {result['chunk_count']} chunks")
        except Exception as e:
            tqdm.write(f"  ✗ {title}: {e}")

    print("  规则书导入完成")

    # 3. 导入卡牌数据
    print("\n[3/3] 导入卡牌数据...")
    card_data_dir = Path('../digimon_card_data')
    if card_data_dir.exists():
        files = list(card_data_dir.glob('*.json'))
        print(f"找到 {len(files)} 个文件\n")
        
        success = 0
        failed = 0
        total_chunks = 0
        
        with tqdm(files, desc="卡牌数据", unit="file", ncols=80) as pbar:
            for file_path in pbar:
                try:
                    title = file_path.stem
                    if title.startswith('digimon_cards_'):
                        title = title[len('digimon_cards_'):]
                    
                    # 更新进度条描述
                    short_title = title[:20] + "..." if len(title) > 20 else title
                    pbar.set_postfix_str(short_title)
                    
                    content = file_path.read_bytes()
                    text = extract_text_from_bytes(content, file_path.name)
                    
                    if not text.strip():
                        continue
                    
                    metadata = DocumentMetadata(
                        doc_type=DocumentType.RULE,
                        title=title,
                        source=str(file_path),
                        tags=['dtcg卡牌数据库']
                    )
                    
                    result = vector_store.add_document(text, metadata)
                    total_chunks += result['chunk_count']
                    success += 1
                except Exception as e:
                    failed += 1
                    tqdm.write(f"  ✗ {file_path.name}: {e}")
        
        print(f"\n卡牌数据导入完成: 成功 {success}, 失败 {failed}, 总计 {total_chunks} chunks")
    else:
        print("  卡牌数据目录不存在")

    print("\n" + "=" * 50)
    print("重建完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="向量数据库管理工具")
    parser.add_argument("--import-rules", nargs='*', metavar="FILE",
                        help="导入规则书文件（不指定文件则弹出选择框）")
    
    args = parser.parse_args()
    
    if args.import_rules is not None:
        # 导入规则书模式
        import_rule_files(args.import_rules if args.import_rules else None)
    else:
        # 重建全部
        rebuild_all()
