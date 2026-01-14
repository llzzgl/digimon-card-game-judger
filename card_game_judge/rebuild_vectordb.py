"""
重建向量数据库 - 使用新的多语言 embedding 模型
运行前会清空现有数据！
"""
import os
import shutil
import time

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

from tqdm import tqdm

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
from pathlib import Path

# 1. 导入术语对照表
print("\n[1/2] 导入术语对照表...")
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

# 2. 导入卡牌数据
print("\n[2/2] 导入卡牌数据...")
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
