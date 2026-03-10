# RAG 系统文档

基于 OpenClaw 架构设计的新一代 RAG (Retrieval-Augmented Generation) 系统。

## 📋 目录

- [架构概览](#架构概览)
- [核心组件](#核心组件)
- [快速开始](#快速开始)
- [高级用法](#高级用法)
- [配置说明](#配置说明)
- [迁移指南](#迁移指南)

---

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                      RAGManager                         │
│  (统一入口，协调所有组件)                                 │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌──────────┐
│Embeddings│      │ ChromaDB │
│Provider  │      │ (向量库)  │
└─────────┘      └──────────┘
    │                 │
    └────────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐    ┌─────────────┐
│  Search  │    │   Chunker   │
│  Engine  │    │  (文档分块)  │
└──────────┘    └─────────────┘
    │
    ▼
┌──────────────┐
│Prompt Builder│
│ (结构化输出)  │
└──────────────┘
```

### 设计原则

1. **模块化**: 每个组件职责单一，可独立测试和替换
2. **可扩展**: 支持多种嵌入提供商和搜索策略
3. **类型安全**: 使用 Enum 和 dataclass 确保类型正确
4. **性能优化**: 混合搜索、重排序、缓存机制

---

## 核心组件

### 1. RAGManager (管理器)

**职责**: 统一入口，协调所有组件

**主要方法**:
```python
# 添加文档
add_document(content: str, metadata: DocumentMetadata) -> Dict

# 搜索文档
search(query: str, doc_types: List[DocumentType], mode: SearchMode, top_k: int) -> List[SearchResult]

# 精确搜索卡牌
search_card_by_number(card_no: str) -> Optional[Dict]

# 构建 Prompt
build_prompt(query: str, search_results: List[SearchResult], card_data: List[Dict]) -> str

# 列出文档
list_documents(doc_type: Optional[DocumentType]) -> List[Dict]

# 删除文档
delete_document(doc_id: str, doc_type: DocumentType) -> bool
```

### 2. EmbeddingProvider (嵌入提供商)

**支持的提供商**:
- `local`: 本地 HuggingFace 模型 (BAAI/bge-m3)
- `openai`: OpenAI Embeddings API
- `gemini`: Google Gemini Embeddings
- `ollama`: Ollama 本地服务

**特点**:
- 统一接口，易于切换
- 支持批量嵌入
- 自动错误处理

### 3. HybridSearchEngine (混合搜索引擎)

**搜索模式**:
- `VECTOR`: 纯向量相似度搜索
- `KEYWORD`: 关键词匹配 (BM25)
- `HYBRID`: 向量 + 关键词混合

**特性**:
- MMR (Maximal Marginal Relevance) 重排序
- 时间衰减 (可选)
- 分数归一化

### 4. DocumentChunker (文档分块器)

**分块策略**:
- **递归分块**: 适用于规则文档，按段落 → 句子 → 字符递归分割
- **QA 分块**: 适用于裁定文档，识别 Q&A 格式
- **卡牌分块**: 适用于卡牌数据，按字段分割

**配置**:
```python
ChunkConfig(
    chunk_size=500,      # 块大小
    chunk_overlap=50     # 重叠大小
)
```

### 5. PromptBuilder (Prompt 构建器)

**功能**:
- 结构化 Prompt 模板
- 按文档类型分组 (规则/裁定/卡牌)
- 自动添加引用来源
- 清晰的回答要求

**输出格式**:
```
你是数码宝贝卡牌游戏的专业裁判助手...

【相关规则】
1. [规则内容]
   来源: [文档标题 - 版本]

【官方裁定】
1. [裁定内容]
   来源: [文档标题]

【涉及卡牌】
1. [卡牌信息]
   卡号: BT1-001

【玩家问题】
[用户问题]

【回答要求】
1. 基于上述规则和裁定给出准确的裁判意见
2. 引用具体条款
...
```

---

## 快速开始

### 安装依赖

```bash
pip install chromadb sentence-transformers rank-bm25
```

### 基本使用

```python
from app.rag import RAGManager, DocumentType, DocumentMetadata, create_embedding_provider

# 1. 初始化 RAG 管理器
rag = RAGManager(
    persist_dir="data/rag_store",
    embedding_provider=create_embedding_provider("local")
)

# 2. 添加文档
metadata = DocumentMetadata(
    doc_id="rule_001",
    title="基础规则",
    doc_type=DocumentType.RULE,
    source=DocumentSource.OFFICIAL
)
rag.add_document("规则内容...", metadata)

# 3. 搜索
results = rag.search("进化规则", top_k=5)

# 4. 构建 Prompt
prompt = rag.build_prompt("进化时费用会退还吗？", results)

# 5. 发送给 LLM
# answer = llm.generate(prompt)
```

---

## 高级用法

### 1. 多文档类型搜索

```python
# 只搜索规则和裁定，不搜索卡牌
results = rag.search(
    query="进化条件",
    doc_types=[DocumentType.RULE, DocumentType.RULING],
    top_k=5
)
```

### 2. 混合搜索模式

```python
from app.rag import SearchMode

# 向量搜索 (语义相似)
results = rag.search(query, mode=SearchMode.VECTOR)

# 关键词搜索 (精确匹配)
results = rag.search(query, mode=SearchMode.KEYWORD)

# 混合搜索 (推荐)
results = rag.search(query, mode=SearchMode.HYBRID)
```

### 3. 卡牌精确搜索

```python
# 通过卡号精确搜索
card = rag.search_card_by_number("BT1-001")

if card:
    print(f"找到卡牌: {card['name_cn']}")
    print(f"效果: {card['effect']}")
```

### 4. 自定义配置

```python
from app.rag import ChunkConfig, SearchConfig

# 自定义分块配置
chunk_config = ChunkConfig(
    chunk_size=800,      # 更大的块
    chunk_overlap=100    # 更多重叠
)

# 自定义搜索配置
search_config = SearchConfig(
    mode=SearchMode.HYBRID,
    max_results=10,
    min_score=0.5,
    enable_rerank=True,
    rerank_top_k=20
)

rag = RAGManager(
    persist_dir="data/rag_store",
    chunk_config=chunk_config,
    search_config=search_config
)
```

### 5. 批量添加文档

```python
import json
from pathlib import Path

# 批量导入规则文档
rules_dir = Path("规则书")
for rule_file in rules_dir.glob("*.txt"):
    with open(rule_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = DocumentMetadata(
        doc_id=f"rule_{rule_file.stem}",
        title=rule_file.stem,
        doc_type=DocumentType.RULE,
        source=DocumentSource.OFFICIAL
    )
    
    rag.add_document(content, metadata)
    print(f"✅ 添加: {rule_file.name}")
```

---

## 配置说明

### DocumentType (文档类型)

```python
class DocumentType(Enum):
    RULE = "rule"        # 规则文档
    RULING = "ruling"    # 官方裁定
    CARD = "card"        # 卡牌数据
```

### DocumentSource (文档来源)

```python
class DocumentSource(Enum):
    OFFICIAL = "official"    # 官方文档
    DATABASE = "database"    # 数据库
    USER = "user"            # 用户上传
```

### SearchMode (搜索模式)

```python
class SearchMode(Enum):
    VECTOR = "vector"      # 向量搜索
    KEYWORD = "keyword"    # 关键词搜索
    HYBRID = "hybrid"      # 混合搜索
```

---

## 迁移指南

### 从旧 VectorStore 迁移

1. **备份数据**
   ```bash
   cp -r data/chroma_db data/chroma_db.backup
   ```

2. **运行迁移脚本**
   ```bash
   # 预览迁移计划
   python migrate_to_new_rag.py --dry-run
   
   # 执行迁移
   python migrate_to_new_rag.py
   ```

3. **验证迁移结果**
   ```python
   from app.rag import RAGManager
   
   rag = RAGManager(persist_dir="data/rag_store")
   documents = rag.list_documents()
   print(f"迁移了 {len(documents)} 个文档")
   ```

### 代码迁移对照

| 旧代码 | 新代码 |
|--------|--------|
| `vector_store.add_document()` | `rag.add_document()` |
| `vector_store.search()` | `rag.search()` |
| `vector_store.search_by_card_number()` | `rag.search_card_by_number()` |
| `vector_store.list_documents()` | `rag.list_documents()` |

---

## 性能优化建议

1. **使用本地嵌入模型**: 避免 API 调用延迟
2. **启用混合搜索**: 提高检索准确率
3. **调整块大小**: 根据文档类型优化
4. **启用重排序**: 提升结果质量
5. **使用卡牌缓存**: 加速卡号查询

---

## 常见问题

### Q: 如何选择嵌入模型？

A: 
- **本地模型** (推荐): 免费，支持中日英，离线可用
- **OpenAI**: 质量高，需要 API key 和网络
- **Gemini**: Google 服务，需要 API key
- **Ollama**: 本地部署，需要额外安装

### Q: 搜索结果不准确怎么办？

A:
1. 尝试混合搜索模式
2. 调整 `min_score` 阈值
3. 启用重排序
4. 增加 `top_k` 获取更多候选

### Q: 如何处理多语言文档？

A: 使用 `BAAI/bge-m3` 模型，支持中日英多语言嵌入

---

## 参考资料

- [OpenClaw RAG 实现](../../../openclaw-main/learning_md/RAG功能实现详解.md)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [BGE-M3 模型](https://huggingface.co/BAAI/bge-m3)

---

**版本**: 1.0.0  
**更新时间**: 2026-03-08
