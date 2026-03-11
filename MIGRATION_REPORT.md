# DTCG Judger 目录结构迁移报告

**迁移时间**: 2026-03-10  
**迁移版本**: 1.0 → 2.0  
**状态**: ✅ 完成

---

## 📋 迁移概述

本次迁移将原有的 `card_game_judge` 目录重构为模块化的 `src` 结构，提升代码组织性和可维护性。

---

## 🏗️ 新目录结构

```
dtcg_judger/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── judger/                   # 裁判核心模块
│   │   ├── __init__.py
│   │   ├── rag/                  # RAG 检索增强生成
│   │   │   ├── __init__.py
│   │   │   ├── manager.py
│   │   │   ├── embeddings.py
│   │   │   ├── search.py
│   │   │   ├── chunker.py
│   │   │   ├── prompt_builder.py
│   │   │   ├── types.py
│   │   │   └── README.md
│   │   ├── llm/                  # LLM 服务（合并版）
│   │   │   ├── __init__.py
│   │   │   └── service.py        # 合并 llm_service.py + enhanced_llm_service.py
│   │   ├── memory/               # 记忆管理系统
│   │   │   ├── __init__.py
│   │   │   ├── memory_manager.py
│   │   │   ├── memory_summarizer.py
│   │   │   └── memory_config.py
│   │   ├── query/                # 查询处理器（合并版）
│   │   │   ├── __init__.py
│   │   │   └── processor.py      # 合并 query_processor.py + enhanced_query_processor.py
│   │   └── api/                  # API 接口
│   │       ├── __init__.py
│   │       └── routes.py         # 从 api.py 迁移
│   ├── scraper/                  # 爬虫模块（合并）
│   │   ├── jp/                   # 日文卡牌爬虫
│   │   └── qa/                   # QA 爬虫
│   ├── translation/              # 翻译模块
│   ├── finetune/                 # 微调模块
│   └── skill/                    # OpenClaw Skill（复制）
├── card_game_judge/              # 原有目录（保留兼容性）
│   └── main.py                   # 兼容入口
├── data/                         # 数据目录
├── docs/                         # 文档目录
└── ...
```

---

## ✅ 迁移清单

### 1. RAG 模块
- [x] 复制 `card_game_judge/app/rag/` → `src/judger/rag/`
- [x] 包含所有子文件：manager.py, embeddings.py, search.py, chunker.py, prompt_builder.py, types.py, README.md
- [x] 创建 `__init__.py` 导出主要类

### 2. LLM 服务（合并）
- [x] 合并 `llm_service.py` + `enhanced_llm_service.py` → `src/judger/llm/service.py`
- [x] 保留两个类：`LLMService`（基础）和 `EnhancedLLMService`（增强）
- [x] 提供工厂函数：`create_llm_service()`, `create_enhanced_llm_service()`
- [x] 创建 `__init__.py`

### 3. 查询处理器（合并）
- [x] 合并 `query_processor.py` + `enhanced_query_processor.py` → `src/judger/query/processor.py`
- [x] 使用继承结构：`EnhancedQueryProcessor` 继承 `QueryProcessor`
- [x] 提供两个单例：`query_processor`, `enhanced_query_processor`
- [x] 创建 `__init__.py`

### 4. 记忆系统
- [x] 迁移 `memory_manager.py` → `src/judger/memory/`
- [x] 迁移 `memory_summarizer.py` → `src/judger/memory/`
- [x] 迁移 `memory_config.py` → `src/judger/memory/`
- [x] 创建 `__init__.py` 导出所有类

### 5. API 接口
- [x] 迁移 `api.py` → `src/judger/api/routes.py`
- [x] 创建 `__init__.py` 导出 FastAPI app

### 6. 爬虫模块（合并）
- [x] 复制 `card_data_scraper_JP/` → `src/scraper/jp/`
- [x] 复制 `card_game_judge/card_game_QA_manger/` → `src/scraper/qa/`
- [x] 保留所有原始文件和子目录

### 7. 翻译模块
- [x] 复制 `card_game_judge/translation/` → `src/translation/`
- [x] 保留所有翻译脚本和文档

### 8. 微调模块
- [x] 复制 `card_game_judge/finetune/` → `src/finetune/`
- [x] 保留所有训练数据和脚本
- [x] 保留模型输出目录

### 9. Skill 目录
- [x] 复制 `skill/` → `src/skill/`
- [x] 保持 OpenClaw Skill 结构不变

### 10. 兼容性保留
- [x] 保留 `card_game_judge/main.py` 作为兼容入口
- [x] 保留原有 `card_game_judge/` 目录结构
- [x] 不修改原文件，等待测试验证

---

## 🔄 Import 路径更新指南

### 原路径 → 新路径对照表

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `from app.rag import RAGManager` | `from src.judger.rag import RAGManager` | RAG 管理器 |
| `from app.llm_service import llm_service` | `from src.judger.llm import llm_service` | LLM 服务 |
| `from app.enhanced_llm_service import EnhancedLLMService` | `from src.judger.llm import EnhancedLLMService` | 增强 LLM |
| `from app.query_processor import query_processor` | `from src.judger.query import query_processor` | 查询处理器 |
| `from app.enhanced_query_processor import enhanced_query_processor` | `from src.judger.query import enhanced_query_processor` | 增强查询 |
| `from app.memory_manager import memory_manager` | `from src.judger.memory import memory_manager` | 记忆管理 |
| `from app.memory_summarizer import memory_summarizer` | `from src.judger.memory import memory_summarizer` | 记忆总结 |
| `from app.api import app` | `from src.judger.api import app` | FastAPI 应用 |

### 推荐导入方式

```python
# 方式 1: 直接导入模块
from src.judger.rag import RAGManager, DocumentType
from src.judger.llm import LLMService, create_llm_service
from src.judger.memory import MemoryManager, memory_manager
from src.judger.query import QueryProcessor, query_processor

# 方式 2: 导入整个子模块
from src import judger

rag = judger.rag.RAGManager(...)
llm = judger.llm.create_llm_service()
memory = judger.memory.memory_manager
query = judger.query.query_processor

# 方式 3: 使用默认实例
from src.judger.llm import llm_service
from src.judger.query import query_processor, enhanced_query_processor
from src.judger.memory import memory_manager, memory_summarizer
```

---

## 📝 主要变更说明

### 1. LLM 服务合并
**原文件**: 
- `app/llm_service.py` (基础服务)
- `app/enhanced_llm_service.py` (增强服务)

**新文件**: `src/judger/llm/service.py`

**变更**:
- 将两个独立文件合并为一个模块
- `LLMService` 类保持不变
- `EnhancedLLMService` 类保持不变，但改为依赖 `LLMService` 实例
- 提供统一的工厂函数
- 清理冗余导入和配置

### 2. 查询处理器合并
**原文件**:
- `app/query_processor.py` (基础处理器)
- `app/enhanced_query_processor.py` (增强处理器)

**新文件**: `src/judger/query/processor.py`

**变更**:
- 使用继承结构：`EnhancedQueryProcessor(QueryProcessor)`
- 共享卡牌编号标准化逻辑
- 增强版添加场面分析、效果时机检测等功能
- 提供两个单例实例

### 3. 模块聚合
**原结构**: 所有模块平铺在 `app/` 目录下  
**新结构**: 按功能分组到 `src/judger/` 子目录

**优势**:
- 更清晰的职责划分
- 更容易定位代码
- 便于独立测试
- 支持渐进式迁移

---

## 🧪 测试验证步骤

### 1. 基础导入测试
```bash
cd D:\LLMProject\dtcg_judger
python -c "from src.judger.rag import RAGManager; print('✅ RAG 导入成功')"
python -c "from src.judger.llm import llm_service; print('✅ LLM 导入成功')"
python -c "from src.judger.memory import memory_manager; print('✅ Memory 导入成功')"
python -c "from src.judger.query import query_processor; print('✅ Query 导入成功')"
```

### 2. 功能测试
```bash
# 测试 RAG 初始化
python -c "from src.judger.rag import RAGManager; rag = RAGManager('data/rag_store'); print('✅ RAG 初始化成功')"

# 测试查询处理器
python -c "from src.judger.query import query_processor; result = query_processor.extract_card_numbers('BT1-001 的效果'); print(f'✅ 查询处理成功：{result}')"

# 测试记忆系统
python -c "from src.judger.memory import memory_manager; stats = memory_manager.get_statistics(); print(f'✅ 记忆系统正常：{stats[\"total_memories\"]} 条记忆')"
```

### 3. API 启动测试
```bash
# 使用新路径启动 API
cd card_game_judge
python main.py  # 应能正常启动
```

---

## ⚠️ 注意事项

### 1. 兼容性
- 原 `card_game_judge/` 目录保持不变
- 所有原文件保留，不做修改
- 等待完整测试通过后再考虑清理

### 2. 依赖关系
- 新模块使用相对导入
- 确保 `src/` 在 Python 路径中
- 可能需要更新 `PYTHONPATH` 或 `sys.path`

### 3. 配置文件
- `.env` 文件位置不变
- 配置加载逻辑不变
- 环境变量名称不变

### 4. 数据路径
- 向量库路径：`data/rag_store` (不变)
- 记忆存储：`data/memory` (不变)
- 卡牌数据：`data/cards` (不变)

---

## 📊 迁移统计

| 模块 | 文件数 | 代码行数 | 状态 |
|------|--------|----------|------|
| RAG | 8 | ~1200 | ✅ 完成 |
| LLM | 1 (合并) | ~450 | ✅ 完成 |
| Query | 1 (合并) | ~550 | ✅ 完成 |
| Memory | 3 | ~800 | ✅ 完成 |
| API | 1 | ~400 | ✅ 完成 |
| Scraper | 20+ | ~2000 | ✅ 完成 |
| Translation | 8 | ~600 | ✅ 完成 |
| Finetune | 30+ | ~3000 | ✅ 完成 |
| Skill | 10+ | ~1000 | ✅ 完成 |
| **总计** | **80+** | **~10000** | **✅ 完成** |

---

## 🚀 下一步计划

1. **测试验证** (优先级：高)
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] API 端点测试

2. **更新入口** (优先级：中)
   - [ ] 更新 `card_game_judge/main.py` 导入路径
   - [ ] 创建新的启动脚本 `src/main.py`
   - [ ] 更新文档

3. **清理优化** (优先级：低)
   - [ ] 删除冗余文件
   - [ ] 更新 `.gitignore`
   - [ ] 优化依赖管理

4. **文档完善** (优先级：中)
   - [ ] 更新 README.md
   - [ ] 编写 API 文档
   - [ ] 添加使用示例

---

## 📞 问题反馈

如遇到问题，请检查：
1. Python 路径是否包含 `src/`
2. 依赖是否完整安装
3. 配置文件是否正确
4. 数据目录是否存在

**迁移负责人**: structure-agent  
**报告生成时间**: 2026-03-10 23:45
