# DTCG Translation Skill

数码宝贝卡牌游戏 (DTCG) 翻译技能包

## 📋 功能概述

本 Skill 提供完整的 DTCG 翻译功能，包括：

- **规则书翻译**: 日文 PDF → 中文文本
- **QA 翻译**: 日文问答 JSON → 中文问答 JSON
- **卡牌翻译**: 日文卡牌数据 → 中文卡牌数据
- **术语管理**: 自动加载和使用术语对照表
- **多引擎支持**: OpenAI / Gemini / 通义千问

## 🏗️ 项目结构

```
translation_skill/
├── src/                      # 源代码
│   ├── __init__.py
│   ├── translator.py         # 翻译统一接口
│   ├── config/               # 配置
│   │   └── translation_config.py
│   ├── engines/              # 翻译引擎
│   │   ├── openai_engine.py
│   │   ├── gemini_engine.py
│   │   └── qwen_engine.py
│   ├── tasks/                # 翻译任务
│   │   ├── rulebook_trans.py # 规则书翻译
│   │   ├── qa_trans.py       # QA 翻译
│   │   └── card_trans.py     # 卡牌翻译
│   └── utils/                # 工具函数
│       ├── terminology.py    # 术语管理
│       └── pdf_parser.py     # PDF 解析
├── data/                     # 数据目录
│   ├── input/                # 输入文件
│   ├── output/               # 输出文件
│   └── terminology/          # 术语表
├── tests/                    # 测试文件
│   ├── test_engines.py       # 引擎测试
│   └── test_integration.py   # 集成测试
├── quick_start.py            # 快速开始脚本
└── README.md
```

## ⚙️ 配置

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# OpenAI 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Gemini 配置
GEMINI_API_KEY=your_api_key
GOOGLE_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# 通义千问配置
DASHSCOPE_API_KEY=your_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 代理配置（可选）
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

## 🚀 快速开始

### 1. 规则书翻译

```python
from src.tasks.rulebook_trans import RulebookTranslator

# 创建翻译器
translator = RulebookTranslator(
    chinese_ref_path="数码宝贝卡牌对战 综合规则 1.2.pdf",
    japanese_path="general_rule.pdf",
    engine_type="openai"  # 或 "gemini", "qwen"
)

# 执行翻译
stats = translator.translate_rulebook()
print(f"翻译完成：{stats['output_file']}")
```

命令行方式：

```bash
cd translation_skill
python -m src.tasks.rulebook_trans <日文 PDF 路径> [中文参考 PDF 路径] [引擎]
```

### 2. QA 翻译

```python
from src.tasks.qa_trans import QATranslator

# 创建翻译器
translator = QATranslator(
    engine_type="qwen"
)

# 加载数据
translator.load_data()

# 执行翻译
stats = translator.translate_all(
    batch_size=10,
    delay=1.0,
    max_count=100  # 或 None 翻译全部
)
```

命令行方式：

```bash
python -m src.tasks.qa_trans
```

### 3. 卡牌翻译

```python
from src.tasks.card_trans import CardTranslator

# 创建翻译器
translator = CardTranslator(engine_type="qwen")

# 加载数据
translator.load_data()

# 执行翻译
stats = translator.translate_all(max_count=50)
```

### 4. 直接使用翻译引擎

```python
from src.translator import Translator

# 创建翻译器
translator = Translator(default_engine="qwen")

# 翻译文本
japanese = "このデジモンは攻撃できない。"
chinese = translator.translate(japanese)
print(chinese)

# 批量翻译
texts = ["テキスト 1", "テキスト 2"]
results = translator.translate_batch(texts)
```

### 5. 术语管理

```python
from src.utils.terminology import TerminologyManager

# 创建术语管理器
manager = TerminologyManager()

# 加载术语表
terms = manager.load_all()

# 查找术语
cn = manager.get_term("バトルエリア")  # → "战斗区"

# 替换文本中的术语
text = "バトルエリアでレスト"
replaced = manager.replace_terminology(text)
# → "战斗区中休眠"
```

## 🔧 高级功能

### 断点续传

QA 翻译支持断点续传，自动保存检查点：

```python
# 中断后重新运行会自动从检查点恢复
translator.translate_all()
```

### 术语表定制

```python
from src.utils.terminology import TerminologyManager

# 使用自定义术语表路径
custom_paths = [
    "path/to/custom_terms.json"
]
manager = TerminologyManager(custom_paths)
manager.load_all()
```

### 输出路径配置

```python
from config.translation_config import TranslationConfig

# 获取输出路径
rules_path = TranslationConfig.get_output_path("rules")
rulings_path = TranslationConfig.get_output_path("rulings")
terms_path = TranslationConfig.get_output_path("terms")
```

## 🧪 测试

运行单元测试：

```bash
cd translation_skill
python -m tests.test_engines
```

运行集成测试：

```bash
python -m tests.test_integration
```

运行所有测试：

```bash
python -m unittest discover tests
```

## 📊 输出格式

### 规则书输出

- 文件：`skill/data/rules.txt`
- 格式：纯文本
- 编码：UTF-8

### QA 输出

- 文件：`skill/data/rulings.json`
- 格式：JSON 数组
- 字段：
  ```json
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
  ```

### 术语表输出

- 文件：`skill/data/terms.json`
- 格式：JSON 对象
- 结构：`{"日文术语": "中文翻译"}`

## ⚠️ 注意事项

1. **API 配额**: 不同引擎有不同的配额限制，Qwen 支持多模型自动切换
2. **网络要求**: Gemini 需要特殊网络环境，OpenAI/Qwen 国内可直接使用
3. **术语一致性**: 翻译会自动使用项目术语表，确保翻译一致性
4. **输出路径**: 默认输出到 `skill/data/` 目录，保持与原项目一致
5. **错误处理**: 翻译失败会保留原文并记录错误信息

## 🛠️ 依赖

```txt
openai>=1.0.0
google-generativeai>=0.3.0
pypdf>=3.0.0
python-dotenv>=1.0.0
httpx>=0.24.0
```

安装依赖：

```bash
pip install openai google-generativeai pypdf python-dotenv httpx
```

## 📝 许可证

与原项目保持一致

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

DTCG Judger Team
