"""导入术语对照表到知识库"""
import sys
import os

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, '.')
from app.vector_store import vector_store
from app.pdf_processor import extract_text_from_bytes
from app.models import DocumentType, DocumentMetadata
from pathlib import Path

files = [
    ('../digimon_data/dtcg_terminology.json', 'DTCG术语对照表'),
    ('../digimon_data/digimon_name_mapping.json', 'DTCG数码宝贝名称对照表')
]

for file_path, title in files:
    p = Path(file_path)
    content = p.read_bytes()
    text = extract_text_from_bytes(content, p.name)
    
    metadata = DocumentMetadata(
        doc_type=DocumentType.RULE,
        title=title,
        source=str(p),
        tags=['术语', '翻译', '日中对照']
    )
    
    result = vector_store.add_document(text, metadata)
    print(f"✓ {title} ({result['chunk_count']} chunks)")

print("导入完成")
