# DTCG Translation Skill 重构报告

## 📋 项目概述

**项目名称**: DTCG Translation Skill  
**重构日期**: 2026-03-12  
**重构目标**: 将现有翻译功能重构为独立 Skill，不影响主裁定功能

---

## ✅ 任务完成情况

### 1. 代码分析 ✓

#### 现有翻译功能分析

**规则书翻译** (`src/translation/`)
- `run_translation.py` - 启动脚本（菜单驱动）
- `translate_rulebook.py` - 主翻译逻辑（基础版）
- `translate_rulebook_openai.py` - OpenAI 引擎实现
- `translate_rulebook_gemini.py` - Gemini 引擎实现
- `import_terminology.py` - 术语导入脚本

**核心流程**:
1. 从 PDF 提取文本（中文参考 + 日文原版）
2. 使用 LLM 从中文参考提取术语
3. 分割日文文本为块
4. 逐块翻译（使用术语对照）
5. 合并输出

**QA 翻译** (`src/scraper/qa/card_game_QA_manger/`)
- `translate_qa.py` - 基础翻译（术语替换 + Google Translate）
- `translate_qa_with_terminology.py` - 多 LLM 翻译（Qwen/Gemini/Ollama）
- `translate_single_qa.py` - 单条测试工具
- 其他辅助脚本

**核心特性**:
- 术语表集成（多个 JSON 文件）
- 卡牌数据集成（卡号映射）
- 批量翻译支持
- 断点续传功能
- 多引擎支持（Qwen 模型自动切换）

**术语管理** (`digimon_card_data/term_mapping/`)
- `game_mechanics_keywords.json` - 游戏机制术语（~140 条）
- `llm_keywords_cn_jp.json` - LLM 提取术语（~900 条）
- `basic_terms_cn_jp.json` - 基础术语
- 格式：`{"中文术语": ["日文术语 1", "日文术语 2"]}`

---

### 2. Translation Skill 结构创建 ✓

已创建完整的 Skill 目录结构：

```
translation_skill/
├── src/
│   ├── __init__.py                    ✓ 包初始化
│   ├── translator.py                  ✓ 翻译统一接口
│   ├── engines/
│   │   ├── __init__.py                ✓
│   │   ├── openai_engine.py           ✓ OpenAI 引擎
│   │   ├── gemini_engine.py           ✓ Gemini 引擎
│   │   └── qwen_engine.py             ✓ 通义千问引擎
│   ├── tasks/
│   │   ├── __init__.py                ✓
│   │   ├── rulebook_trans.py          ✓ 规则书翻译
│   │   ├── qa_trans.py                ✓ QA 翻译
│   │   └── card_trans.py              ✓ 卡牌翻译
│   └── utils/
│       ├── __init__.py                ✓
│       ├── terminology.py             ✓ 术语管理
│       └── pdf_parser.py              ✓ PDF 解析
├── config/
│   └── translation_config.py          ✓ 配置管理
├── data/
│   ├── input/                         ✓ 输入目录
│   ├── output/                        ✓ 输出目录
│   └── terminology/                   ✓ 术语表目录
├── tests/
│   ├── __init__.py                    ✓
│   ├── test_engines.py                ✓ 引擎单元测试
│   └── test_integration.py            ✓ 集成测试
└── README.md                          ✓ 使用文档
```

**文件统计**:
- Python 源文件：14 个
- 测试文件：2 个
- 文档：2 个（README + 报告）
- 总代码行数：~2000 行

---

### 3. 重构要求遵循 ✓

| 要求 | 状态 | 说明 |
|------|------|------|
| 不改动原有翻译文件 | ✅ | 原 `src/translation/` 和 `src/scraper/qa/` 保持原样 |
| 新建测试文件夹 | ✅ | `translation_skill/data/` 已创建 |
| 输出路径一致 | ✅ | 默认输出到 `skill/data/rules.txt/rulings.json/terms.json` |

---

### 4. 实现要点 ✓

#### 4.1 统一翻译接口设计 ✓

**Translator 类** (`src/translator.py`):
```python
class Translator:
    - 统一管理多个翻译引擎
    - 自动故障转移（引擎不可用时切换）
    - 支持单文本和批量翻译
    - 上下文传递（术语表、卡牌信息等）
```

**TranslationEngine 基类**:
```python
class TranslationEngine(ABC):
    - initialize() - 初始化引擎
    - translate_text() - 翻译单文本
    - translate_batch() - 批量翻译
    - is_available() - 检查可用性
```

#### 4.2 多引擎支持 ✓

| 引擎 | 文件 | 特性 |
|------|------|------|
| OpenAI | `openai_engine.py` | 支持代理、自定义 base_url、错误重试 |
| Gemini | `gemini_engine.py` | 支持代理、错误重试 |
| Qwen | `qwen_engine.py` | **多模型自动切换**（配额用尽时） |

**Qwen 模型列表**:
1. `qwen-turbo` - 快速、便宜
2. `qwen-plus` - 平衡（默认）
3. `qwen-max` - 高质量
4. `qwen-long` - 长文本

#### 4.3 术语映射集成 ✓

**TerminologyManager 类** (`src/utils/terminology.py`):
- 自动加载项目术语表（3 个默认文件）
- 支持多种术语表格式
- 术语查找（精确匹配 + 部分匹配）
- 文本术语替换（长术语优先）
- 术语统计信息

**集成方式**:
```python
# 所有翻译任务自动加载术语表
terminology_manager = load_terminology_from_project(project_root)
context = {"terminology": terminology_manager.terminology}
translated = translator.translate(text, context=context)
```

#### 4.4 批量翻译支持 ✓

**批量处理特性**:
- 可配置 batch_size（默认 10）
- 批次间延迟（避免 API 限流）
- 进度显示
- 错误处理（保留原文）

**断点续传**（QA 翻译）:
- 自动保存检查点（`.checkpoint.json`）
- 中断后自动恢复
- 完成后自动删除检查点

#### 4.5 翻译质量检查 ✓

**质量保障措施**:
1. **术语一致性**: 强制使用术语表
2. **完全翻译**: 提示词强调不保留日文
3. **格式保持**: JSON 结构、PDF 段落结构
4. **错误记录**: 翻译失败记录错误信息
5. **原文保留**: `*_original` 字段保存原文

**提示词优化**:
- 详细的翻译规则
- 正误示例对比
- 术语对照表（前 100 条）
- 卡牌上下文信息

#### 4.6 错误处理和重试 ✓

**重试机制**:
```python
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # 指数退避
REQUEST_TIMEOUT = 60
```

**错误处理**:
- API 调用失败：重试
- 配额用尽（Qwen）：自动切换模型
- 翻译失败：保留原文 + 记录错误
- 文件不存在：明确错误信息
- 键盘中断：保存进度

---

### 5. 测试 ✓

#### 5.1 单元测试 (`test_engines.py`)

**测试覆盖**:
- `TestOpenAIEngine`: 初始化、短文本翻译、术语翻译
- `TestGeminiEngine`: 初始化、短文本翻译
- `TestQwenEngine`: 初始化、短文本翻译、模型切换
- `TestBatchTranslation`: 批量翻译

**运行方式**:
```bash
python -m tests.test_engines
```

#### 5.2 集成测试 (`test_integration.py`)

**测试覆盖**:
- `TestTerminologyManager`: 术语加载、查找、替换
- `TestPDFParser`: 文本分割
- `TestQATranslator`: 创建、数据加载、单条翻译
- `TestRulebookTranslator`: 创建、文本分块
- `TestOutputFormat`: 输出格式验证

**运行方式**:
```bash
python -m tests.test_integration
```

---

## 📊 对比分析

### 原翻译功能 vs Translation Skill

| 特性 | 原功能 | Skill | 改进 |
|------|--------|-------|------|
| **代码组织** | 分散在多个目录 | 统一 Skill 结构 | ✅ 更清晰 |
| **引擎接口** | 各自实现 | 统一基类 | ✅ 易扩展 |
| **术语管理** | 硬编码路径 | 配置化 + 自动加载 | ✅ 更灵活 |
| **错误处理** | 基础重试 | 完善重试 + 故障转移 | ✅ 更可靠 |
| **测试覆盖** | 无 | 单元测试 + 集成测试 | ✅ 新增 |
| **文档** | 代码注释 | README + 报告 | ✅ 更完善 |
| **配置管理** | 环境变量散乱 | 统一配置类 | ✅ 更规范 |
| **输出路径** | 分散 | 统一配置 | ✅ 更一致 |

### 保留的原功能特性

1. **多引擎支持**: OpenAI/Gemini/Qwen 全部保留
2. **术语表集成**: 所有现有术语表继续使用
3. **断点续传**: QA 翻译的检查点功能保留
4. **批量翻译**: 批次处理、延迟控制保留
5. **PDF 解析**: pypdf 文本提取保留

---

## 🎯 输出验证

### 输出路径

所有翻译输出默认路径（与原要求一致）:

```
skill/data/
├── rules.txt       # 规则书翻译
├── rulings.json    # QA 翻译
└── terms.json      # 术语表
```

### 输出格式

**rules.txt** (规则书):
- 纯文本格式
- UTF-8 编码
- 段落结构保持

**rulings.json** (QA):
```json
[
  {
    "qa_number": "QA-001",
    "question": "中文问题",
    "answer": "中文答案",
    "question_original": "日文问题",
    "answer_original": "日文答案",
    "language": "zh-cn",
    "translated_from": "ja",
    "translation_method": "llm_qwen"
  }
]
```

**terms.json** (术语表):
```json
{
  "バトルエリア": "战斗区",
  "レスト": "休眠",
  "デジモン": "数码兽"
}
```

---

## 📦 依赖管理

### 核心依赖

```txt
# LLM SDK
openai>=1.0.0              # OpenAI + Qwen (兼容接口)
google-generativeai>=0.3.0 # Gemini

# PDF 处理
pypdf>=3.0.0

# 配置
python-dotenv>=1.0.0

# HTTP 客户端（代理支持）
httpx>=0.24.0
```

### 安装命令

```bash
pip install openai google-generativeai pypdf python-dotenv httpx
```

---

## 🔧 使用示例

### 示例 1: 规则书翻译

```python
from src.tasks.rulebook_trans import RulebookTranslator

translator = RulebookTranslator(
    chinese_ref_path="数码宝贝卡牌对战 综合规则 1.2.pdf",
    japanese_path="general_rule.pdf",
    engine_type="qwen"  # 推荐：性价比高
)

stats = translator.translate_rulebook()
# 输出：skill/data/rules.txt
```

### 示例 2: QA 翻译

```python
from src.tasks.qa_trans import QATranslator

translator = QATranslator(engine_type="qwen")
translator.load_data()

# 测试模式（前 10 条）
stats = translator.translate_all(max_count=10)

# 完整翻译
stats = translator.translate_all()
# 输出：skill/data/rulings.json
```

### 示例 3: 直接翻译

```python
from src.translator import Translator

translator = Translator(default_engine="qwen")

# 单文本
text = "このデジモンは攻撃できない。"
result = translator.translate(text)

# 批量翻译
texts = ["テキスト 1", "テキスト 2"]
results = translator.translate_batch(texts, delay=0.5)
```

---

## 🚀 后续优化建议

### 短期优化

1. **增加日志系统**: 记录翻译过程、错误详情
2. **翻译缓存**: 避免重复翻译相同文本
3. **质量评分**: 使用 LLM 评估翻译质量
4. **并行翻译**: 提高大批量翻译速度

### 中期优化

1. **Web 界面**: 提供可视化翻译界面
2. **术语提取优化**: 更智能的术语识别
3. **上下文感知**: 跨块上下文传递
4. **翻译记忆库**: TM 系统支持

### 长期优化

1. **微调模型**: 针对 DTCG 微调翻译模型
2. **多语言支持**: 扩展到韩文、英文等
3. **API 服务**: 提供翻译 API 接口
4. **协作翻译**: 支持人工校对流程

---

## 📝 总结

### 已完成

✅ 完整的代码分析  
✅ Skill 结构创建（14 个源文件）  
✅ 统一翻译接口设计  
✅ 三引擎支持（OpenAI/Gemini/Qwen）  
✅ 术语管理集成  
✅ 批量翻译支持  
✅ 错误处理和重试机制  
✅ 单元测试和集成测试  
✅ 完整文档（README + 报告）  

### 核心优势

1. **模块化**: 清晰的代码组织，易于维护
2. **可扩展**: 统一接口，轻松添加新引擎
3. **可靠性**: 完善的错误处理和重试机制
4. **一致性**: 术语表集成确保翻译一致
5. **灵活性**: 多引擎支持，适应不同场景
6. **兼容性**: 不改动原有代码，独立运行

### 使用建议

1. **首次使用**: 先运行测试验证配置
2. **小规模测试**: 使用 `max_count` 参数测试
3. **选择引擎**: 国内推荐 Qwen，海外可选 OpenAI/Gemini
4. **监控配额**: Qwen 支持自动切换，但仍需注意配额
5. **保留检查点**: 大批量翻译利用断点续传

---

**报告生成时间**: 2026-03-12  
**重构执行者**: DTCG Judger Team  
**版本**: 1.0.0
