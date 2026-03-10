# QA翻译工具使用指南

## 功能说明

`translate_qa_with_terminology.py` 是一个使用大语言模型和专有名词表进行高质量日文QA翻译的工具。

## 支持的LLM

1. **Qwen (通义千问)** - 推荐，国内访问快，无需代理
2. **Gemini** - Google的模型，可能需要代理
3. **Ollama** - 本地运行，需要先安装Ollama

## 使用前准备

### 1. 安装依赖

```bash
# 如果使用Qwen或Ollama
pip install openai

# 如果使用Gemini
pip install google-generativeai
```

### 2. 配置API密钥

在 `card_game_judge/.env` 文件中设置对应的API密钥：

```env
# 通义千问
DASHSCOPE_API_KEY=sk-xxxxx

# Gemini (可选)
GEMINI_API_KEY=xxxxx
# 或
GOOGLE_API_KEY=xxxxx

# OpenAI (可选)
OPENAI_API_KEY=sk-xxxxx
```

### 3. 准备数据文件

确保以下文件存在：

- `digimon_card_data/term_mapping/game_mechanics_keywords.json` - 游戏术语表
- `digimon_card_data/digimon_card_data_chiness/digimon_cards_cn.json` - 中文卡牌数据
- `card_game_judge/card_game_QA_manger/official_qa_jp.json` - 日文QA数据

## 使用方法

### 方法1: 交互式运行

```bash
cd card_game_judge/card_game_QA_manger
python translate_qa_with_terminology.py
```

然后按提示选择：
1. 选择LLM类型 (1=Qwen, 2=Gemini, 3=Ollama)
2. 选择翻译模式 (1=测试10条, 2=翻译100条, 3=全部翻译)

### 方法2: 代码调用

```python
from translate_qa_with_terminology import MultiLLMQATranslator

# 创建翻译器
translator = MultiLLMQATranslator(llm_type="qwen")

# 翻译前10条（测试）
translator.translate_all(batch_size=5, delay=1.0, max_count=10)

# 翻译全部
translator.translate_all(batch_size=10, delay=1.0)
```

## 翻译特性

### 1. 使用专有名词表

工具会自动加载 `game_mechanics_keywords.json` 中的游戏术语，确保翻译的一致性：

- 登場時 → 登场时
- アタック → 攻击
- デッキ → 卡组
- 等等...

### 2. 卡牌名称映射

如果QA中包含卡号，工具会自动使用对应的中文卡名。

### 3. 断点续传

翻译过程中如果中断（Ctrl+C或出错），会自动保存进度到检查点文件。下次运行时会自动从上次中断的地方继续。

检查点文件：`official_qa_cn_{llm_type}_checkpoint.json`

### 4. 翻译质量

- 使用专业的翻译提示词
- 保持游戏术语的准确性
- 确保中文表达的流畅性
- 保留原文的完整信息

## 输出文件

翻译完成后会生成：

- `official_qa_cn_qwen.json` - 使用Qwen翻译的结果
- `official_qa_cn_gemini.json` - 使用Gemini翻译的结果
- `official_qa_cn_ollama.json` - 使用Ollama翻译的结果

每条翻译的QA包含：
- `question` - 翻译后的问题
- `answer` - 翻译后的答案
- `question_original` - 原始日文问题
- `answer_original` - 原始日文答案
- `card_name` - 中文卡名
- `translation_method` - 翻译方法标记

## 测试工具

### 测试配置和数据

```bash
python test_translation_setup.py
```

这会检查：
- 所有必需文件是否存在
- 术语表和卡牌数据是否正确加载
- API密钥是否配置
- 模块是否能正常导入

## 常见问题

### Q: 提示"请设置DASHSCOPE_API_KEY环境变量"

A: 在 `.env` 文件中添加：
```
DASHSCOPE_API_KEY=sk-你的密钥
```

### Q: Gemini连接失败

A: Gemini需要访问Google服务，可能需要配置代理。建议使用Qwen。

### Q: 翻译速度慢

A: 
- 使用Qwen的qwen-turbo模型（更快但质量稍低）
- 增大batch_size（但要注意API限流）
- 减小delay时间（但要注意API限流）

### Q: 如何清除检查点重新开始

A: 删除检查点文件：
```bash
del official_qa_cn_*_checkpoint.json
```

## 模型选择建议

| 模型 | 速度 | 质量 | 成本 | 推荐场景 |
|------|------|------|------|----------|
| qwen-turbo | 快 | 中 | 低 | 快速测试 |
| qwen-plus | 中 | 高 | 中 | 日常使用（推荐） |
| qwen-max | 慢 | 最高 | 高 | 重要翻译 |
| gemini-2.0-flash-exp | 快 | 高 | 免费 | 有代理时使用 |
| ollama (本地) | 中 | 中 | 免费 | 离线使用 |

## 进阶配置

### 修改模型

编辑 `translate_qa_with_terminology.py`：

```python
# Qwen模型
self.model_name = "qwen-turbo"  # 或 "qwen-plus", "qwen-max"

# Gemini模型
self.client = genai.GenerativeModel('gemini-pro')  # 或其他模型

# Ollama模型
self.model_name = "qwen2:7b"  # 或其他本地模型
```

### 调整翻译参数

```python
translator.translate_all(
    batch_size=20,    # 每批处理数量
    delay=0.5,        # 批次间延迟（秒）
    start_from=100,   # 从第100条开始
    max_count=50      # 只翻译50条
)
```

### 自定义提示词

修改 `_build_translation_prompt()` 方法中的提示词模板。

## 相关文件

- `translate_qa_with_terminology.py` - 主翻译工具
- `test_translation_setup.py` - 配置测试工具
- `translate_qa_with_llm.py` - 旧版翻译工具（不使用术语表）
- `../app/llm_service.py` - LLM服务参考实现
