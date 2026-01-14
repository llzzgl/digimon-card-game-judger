"""测试不同 embedding 模型对日文的支持"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np

# 测试文本
texts = [
    "ウォーグレイモン",  # 战斗暴龙兽
    "アグモン",  # 亚古兽
    "≪ブロッカー≫",  # 阻挡者
    "【進化時】このデジモンの進化元",  # 进化时效果
    "セキュリティアタック",  # 安防攻击
]

query = "ウォーグレイモン 战斗暴龙兽"

# 测试模型
models = [
    ("BAAI/bge-small-zh-v1.5", "中文BGE小"),
    ("BAAI/bge-m3", "多语言BGE-M3"),
    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "多语言MiniLM"),
]

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

for model_name, desc in models:
    print(f"\n{'='*50}")
    print(f"模型: {desc} ({model_name})")
    print('='*50)
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        query_emb = embeddings.embed_query(query)
        
        for text in texts:
            text_emb = embeddings.embed_query(text)
            sim = cosine_similarity(query_emb, text_emb)
            print(f"  {text}: {sim:.4f}")
            
    except Exception as e:
        print(f"  错误: {e}")
