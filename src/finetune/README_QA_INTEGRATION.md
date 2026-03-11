# 官方QA数据集成到微调训练指南

## 📋 概述

你现在有了 `official_qa_cn.json` 文件，包含大量中文官方QA数据。本指南说明如何将这些数据用于微调训练。

## 🔍 当前QA数据情况

**文件位置**: `card_game_judge/card_game_QA_manger/official_qa_cn.json`

**数据格式**:
```json
{
  "id": "5794",
  "question": "问题内容",
  "answer": "答案内容",
  "qa_number": "5794",
  "card_no": "卡牌编号",
  "card_name": "卡牌名称",
  "question_original": "日文原文",
  "answer_original": "日文原文"
}
```

**数据特点**:
- ✅ 包含大量官方裁定问答
- ⚠️ 翻译质量参差不齐（有机翻痕迹）
- ✅ 包含卡牌关联信息
- ✅ 包含日文原文对照

## 🚀 使用流程

### 方案1: 快速集成（推荐）

直接处理并集成到现有微调数据中：

```bash
cd card_game_judge/finetune

# 步骤1: 处理中文QA数据
python process_official_qa_cn.py

# 步骤2: 整合所有数据（规则书+QA+卡牌）
python collect_all_data.py

# 或者使用批处理脚本一键完成
prepare_qa_data.bat
```

**输出文件**:
- `training_data/official_qa_cn_finetune.jsonl` - 仅QA数据
- `training_data/dtcg_finetune_data.jsonl` - 完整训练数据（规则书+QA+卡牌）
- `training_data/official_qa_cn_cleaned.json` - 清理后的QA数据

### 方案2: 改进翻译质量后使用

如果发现翻译质量不佳，可以先改进翻译：

```bash
cd card_game_judge/card_game_QA_manger

# 使用LLM重新翻译（需要配置API）
python translate_qa_with_llm.py

# 或使用本地模型翻译
python translate_qa_local.py

# 然后再处理
cd ../finetune
python process_official_qa_cn.py
```

## 📊 数据处理说明

### `process_official_qa_cn.py` 做了什么？

1. **读取QA数据**: 从 `official_qa_cn.json` 读取
2. **清理文本**: 
   - 移除日期标记
   - 修正常见机翻问题
   - 统一术语
3. **格式转换**: 转换为微调训练格式
   ```python
   {
     "instruction": "你是数码宝贝卡牌游戏(DTCG)的官方裁定专家...",
     "input": "问题内容",
     "output": "【卡牌编号】卡牌名称\n\n答案内容\n\n（官方Q&A #编号）"
   }
   ```
4. **导出多种格式**:
   - JSONL格式（用于微调）
   - JSON格式（便于查看）
   - 对话格式（ChatML）

### `collect_all_data.py` 做了什么？

整合所有训练数据源：
1. **规则书问答** - 从综合规则提取
2. **官方QA** - 从 `official_qa_cn.json` 加载
3. **卡牌数据** - 从卡牌数据库生成
4. **自定义问答** - 场景分析等

最终生成完整的训练数据集。

## 🎯 微调训练

### 使用Gemini微调

```bash
# 准备数据
python collect_all_data.py

# 上传数据并微调（需要配置Gemini API）
python finetune_gemini.py --data training_data/dtcg_finetune_data.jsonl
```

### 使用Qwen本地微调

```bash
# 准备数据
python collect_all_data.py

# 本地微调
python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl
```

## 📈 数据质量评估

### 检查翻译质量

```bash
cd card_game_judge/card_game_QA_manger

# 分析翻译质量
python analyze_translation.py

# 测试翻译效果
python test_translated_qa.py
```

### 查看数据统计

处理完成后会显示：
- 总QA数量
- 各来源分布
- 标签分布
- 卡牌关联情况

## 🔧 自定义配置

### 修改清理规则

编辑 `process_official_qa_cn.py` 中的 `clean_qa_text()` 函数：

```python
def clean_qa_text(text: str) -> str:
    replacements = {
        'か？': '吗？',
        '和して': '作为',
        # 添加更多替换规则...
    }
    # ...
```

### 修改系统指令

编辑 `data_collector.py` 中的 `SYSTEM_INSTRUCTIONS`：

```python
SYSTEM_INSTRUCTIONS = {
    "qa": "你是数码宝贝卡牌游戏(DTCG)的官方裁定专家。请根据官方Q&A回答问题。",
    # 自定义其他指令...
}
```

## 📝 数据格式说明

### 输入格式（official_qa_cn.json）

```json
[
  {
    "id": "5794",
    "question": "安防检查了时、【安防】效果和...",
    "answer": "【安防】效果优先发动...",
    "qa_number": "5794",
    "card_no": "EX11-010",
    "card_name": "マスターティラノモン",
    "question_original": "セキュリティをチェックしたとき...",
    "answer_original": "【セキュリティ】効果が優先して..."
  }
]
```

### 输出格式（微调训练）

**JSONL格式** (每行一个JSON对象):
```json
{"instruction": "系统指令", "input": "问题", "output": "答案"}
{"instruction": "系统指令", "input": "问题", "output": "答案"}
```

**对话格式** (ChatML):
```json
{
  "conversations": [
    {"role": "system", "content": "系统指令"},
    {"role": "user", "content": "问题"},
    {"role": "assistant", "content": "答案"}
  ]
}
```

## ⚠️ 注意事项

1. **翻译质量**: 当前QA数据是机器翻译，可能存在：
   - 日文残留（如"か"、"和して"等）
   - 术语不统一
   - 语句不通顺
   
   建议先运行 `analyze_translation.py` 评估质量

2. **数据量**: 83000+行数据，处理可能需要一些时间

3. **内存占用**: 处理大量数据时注意内存使用

4. **编码问题**: 确保所有文件使用UTF-8编码

## 🎓 最佳实践

1. **先评估再使用**: 
   ```bash
   python analyze_translation.py
   ```

2. **小批量测试**: 先用少量数据测试微调效果

3. **混合数据源**: 结合规则书、QA、卡牌数据效果更好

4. **定期更新**: 官方QA会更新，定期重新爬取和处理

## 🔗 相关文件

- `process_official_qa_cn.py` - QA数据处理脚本
- `collect_all_data.py` - 数据整合脚本
- `data_collector.py` - 数据收集器核心类
- `prepare_qa_data.bat` - 一键处理批处理脚本
- `../card_game_QA_manger/official_qa_cn.json` - 原始QA数据

## 📞 问题排查

### 问题1: 找不到QA文件

**解决**: 确认文件路径
```bash
# 检查文件是否存在
dir ..\card_game_QA_manger\official_qa_cn.json
```

### 问题2: 编码错误

**解决**: 确保使用UTF-8编码
```python
with open(file, 'r', encoding='utf-8') as f:
    data = json.load(f)
```

### 问题3: 内存不足

**解决**: 分批处理或增加虚拟内存

### 问题4: 翻译质量差

**解决**: 使用LLM重新翻译
```bash
cd ../card_game_QA_manger
python translate_qa_with_llm.py
```
