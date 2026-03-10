# Import 路径更新参考

**用途**: 快速查找迁移后的新导入路径  
**版本**: 2.0  
**更新时间**: 2026-03-10

---

## 📦 核心模块导入

### RAG 模块

```python
# 旧路径
from app.rag import RAGManager, DocumentType, DocumentMetadata
from app.rag.manager import RAGManager
from app.rag.types import DocumentType, SearchMode

# 新路径 ✅
from src.judger.rag import RAGManager, DocumentType, DocumentMetadata, DocumentSource, SearchMode
from src.judger.rag.manager import RAGManager
from src.judger.rag.types import DocumentType, SearchMode

# 完整导入
from src.judger.rag import (
    RAGManager,
    DocumentType,
    DocumentMetadata,
    DocumentSource,
    SearchMode,
    create_embedding_provider,
    HybridSearchEngine,
    DocumentChunker,
    PromptBuilder
)
```

### LLM 服务

```python
# 旧路径
from app.llm_service import LLMService, llm_service
from app.enhanced_llm_service import EnhancedLLMService, create_enhanced_llm_service

# 新路径 ✅
from src.judger.llm import LLMService, EnhancedLLMService, llm_service
from src.judger.llm.service import create_llm_service, create_enhanced_llm_service

# 完整导入
from src.judger.llm import (
    LLMService,
    EnhancedLLMService,
    create_llm_service,
    create_enhanced_llm_service,
    llm_service  # 默认实例
)

# 使用示例
from src.judger.llm import create_llm_service, create_enhanced_llm_service

# 创建基础服务
llm = create_llm_service({'model': 'qwen'})

# 创建增强服务
enhanced_llm = create_enhanced_llm_service(llm)
```

### 查询处理器

```python
# 旧路径
from app.query_processor import QueryProcessor, query_processor
from app.enhanced_query_processor import EnhancedQueryProcessor, enhanced_query_processor

# 新路径 ✅
from src.judger.query import QueryProcessor, EnhancedQueryProcessor
from src.judger.query import query_processor, enhanced_query_processor
from src.judger.query.processor import EffectTiming, EffectInfo, ScenarioElement

# 完整导入
from src.judger.query import (
    QueryProcessor,
    EnhancedQueryProcessor,
    query_processor,          # 基础单例
    enhanced_query_processor, # 增强单例
    EffectTiming,
    EffectInfo,
    ScenarioElement
)

# 使用示例
from src.judger.query import query_processor, enhanced_query_processor

# 基础查询分析
cards = query_processor.extract_card_numbers("BT1-001 的效果是什么？")

# 增强场面分析
analysis = enhanced_query_processor.analyze_scenario("我方 BT1-001 和对方 ST1-001 同时触发效果，如何处理？")
```

### 记忆系统

```python
# 旧路径
from app.memory_manager import MemoryManager, memory_manager
from app.memory_summarizer import MemorySummarizer, memory_summarizer
from app.memory_config import MemoryConfig, MemoryType, MemoryImportance

# 新路径 ✅
from src.judger.memory import MemoryManager, MemorySummarizer
from src.judger.memory import memory_manager, memory_summarizer
from src.judger.memory import MemoryConfig, MemoryType, MemoryImportance, default_memory_config

# 完整导入
from src.judger.memory import (
    MemoryManager,
    MemorySummarizer,
    memory_manager,           # 默认实例
    memory_summarizer,        # 默认实例
    MemoryConfig,
    MemoryEntry,
    MemoryType,
    MemoryImportance,
    default_memory_config
)

# 使用示例
from src.judger.memory import memory_manager, MemoryType, MemoryImportance

# 保存记忆
memory = memory_manager.add_memory(
    question="问题内容",
    answer="答案内容",
    summary="总结",
    memory_type=MemoryType.LONG_TERM,
    importance=MemoryImportance.HIGH,
    user_confirmed=True
)

# 搜索记忆
memories = memory_manager.search_memories("进化规则", top_k=5)
```

### API 接口

```python
# 旧路径
from app.api import app
from app import api

# 新路径 ✅
from src.judger.api import app
from src.judger.api.routes import app

# 使用示例
from src.judger.api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 🔧 爬虫模块导入

### 日文卡牌爬虫

```python
# 旧路径
from card_data_scraper_JP.scraper import scrape_card_data
from card_data_scraper_JP.models import CardData

# 新路径 ✅
from src.scraper.jp.scraper import scrape_card_data
from src.scraper.jp.models import CardData
```

### QA 爬虫

```python
# 旧路径
from card_game_judge.card_game_QA_manger.scraper_jp_official import scrape_faq
from card_game_judge.card_game_QA_manger.config import Config

# 新路径 ✅
from src.scraper.qa.scraper_jp_official import scrape_faq
from src.scraper.qa.config import Config
```

---

## 🌐 翻译模块导入

```python
# 旧路径
from card_game_judge.translation.translate_rulebook import translate_text
from card_game_judge.translation.run_translation import run_translation

# 新路径 ✅
from src.translation.translate_rulebook import translate_text
from src.translation.run_translation import run_translation
```

---

## 🎯 微调模块导入

```python
# 旧路径
from card_game_judge.finetune.finetune_qwen import FinetuneConfig
from card_game_judge.finetune.data_collector import collect_data

# 新路径 ✅
from src.finetune.finetune_qwen import FinetuneConfig
from src.finetune.data_collector import collect_data
```

---

## 📋 Skill 模块导入

```python
# 旧路径
from skill.judger import DTCGJudgerSkill
from skill.handlers import handle_query

# 新路径 ✅
from src.skill.judger import DTCGJudgerSkill
from src.skill.handlers import handle_query

# Skill 路径通常保持不变，根据实际结构调整
```

---

## 🚀 快速迁移脚本

如果需要批量更新现有代码中的导入路径，可以使用以下脚本：

```python
# migrate_imports.py
import re
from pathlib import Path

# 导入路径映射
IMPORT_MAP = {
    r'from app\.rag import': 'from src.judger.rag import',
    r'from app\.llm_service import': 'from src.judger.llm import',
    r'from app\.enhanced_llm_service import': 'from src.judger.llm import',
    r'from app\.query_processor import': 'from src.judger.query import',
    r'from app\.enhanced_query_processor import': 'from src.judger.query import',
    r'from app\.memory_manager import': 'from src.judger.memory import',
    r'from app\.memory_summarizer import': 'from src.judger.memory import',
    r'from app\.memory_config import': 'from src.judger.memory import',
    r'from app\.api import': 'from src.judger.api import',
    r'from app\. import': 'from src.judger import',
    r'import app\.': 'import src.judger.',
}

def migrate_file(file_path: Path):
    """迁移单个文件的导入路径"""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    for old_pattern, new_import in IMPORT_MAP.items():
        content = re.sub(old_pattern, new_import, content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已更新：{file_path}")
        return True
    return False

def migrate_directory(dir_path: str):
    """迁移目录下所有 Python 文件"""
    dir_path = Path(dir_path)
    count = 0
    
    for py_file in dir_path.glob("**/*.py"):
        if migrate_file(py_file):
            count += 1
    
    print(f"\n📊 迁移完成：{count} 个文件已更新")

# 使用示例
if __name__ == "__main__":
    # 迁移指定目录
    migrate_directory("card_game_judge")
```

---

## 🧪 测试导入

运行以下命令测试所有导入是否正常：

```bash
# 测试核心模块
python -c "from src.judger.rag import RAGManager; print('✅ RAG')"
python -c "from src.judger.llm import llm_service; print('✅ LLM')"
python -c "from src.judger.query import query_processor; print('✅ Query')"
python -c "from src.judger.memory import memory_manager; print('✅ Memory')"
python -c "from src.judger.api import app; print('✅ API')"

# 测试爬虫模块
python -c "from src.scraper.jp import scraper; print('✅ Scraper JP')"
python -c "from src.scraper.qa import scraper_jp_official; print('✅ Scraper QA')"

# 测试其他模块
python -c "from src.translation import translate_rulebook; print('✅ Translation')"
python -c "from src.finetune import finetune_qwen; print('✅ Finetune')"
```

---

## 📝 常见问题

### Q1: 导入时提示 `ModuleNotFoundError: No module named 'src'`

**解决方案**:
```bash
# 方法 1: 将项目根目录添加到 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:D:\LLMProject\dtcg_judger"

# 方法 2: 在代码中添加
import sys
sys.path.insert(0, r'D:\LLMProject\dtcg_judger')

# 方法 3: 使用绝对导入
# 确保从项目根目录运行 Python
```

### Q2: 相对导入失败

**解决方案**:
```python
# 错误 ❌
from .rag import RAGManager  # 在 src/judger/__init__.py 中

# 正确 ✅
from src.judger.rag import RAGManager
# 或
from .rag.manager import RAGManager  # 在 src/judger/ 内部使用
```

### Q3: 循环导入问题

**解决方案**:
```python
# 在模块级别导入改为在函数内部导入
def my_function():
    from src.judger.other_module import Something
    # 使用 Something
```

---

## 📊 迁移进度追踪

| 模块 | 已迁移文件 | 待迁移文件 | 状态 |
|------|-----------|-----------|------|
| RAG | 8 | 0 | ✅ 100% |
| LLM | 2 (合并为 1) | 0 | ✅ 100% |
| Query | 2 (合并为 1) | 0 | ✅ 100% |
| Memory | 3 | 0 | ✅ 100% |
| API | 1 | 0 | ✅ 100% |
| Scraper | 20+ | 0 | ✅ 100% |
| Translation | 8 | 0 | ✅ 100% |
| Finetune | 30+ | 0 | ✅ 100% |

**总体进度**: 100% ✅

---

**最后更新**: 2026-03-10  
**维护者**: structure-agent
