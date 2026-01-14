"""测试卡牌编号检索"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, '.')
from app.vector_store import vector_store

# 测试卡牌编号检索
queries = ['BT20-079', 'BT23-058', 'ウィザーモン', 'スカルバルキモン']
for q in queries:
    print(f'查询: {q}')
    results = vector_store.search(q, top_k=1, translate_query=False, translate_result=False)
    if results:
        content = results[0]["content"][:200]
        score = results[0]["score"]
        print(f'  分数: {score:.4f}')
        print(f'  结果: {content}')
    else:
        print('  无结果')
    print()
