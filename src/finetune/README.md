# DTCG 规则微调训练

使用 LoRA 对 Qwen2 模型进行 DTCG（数码宝贝卡牌游戏）规则微调。

## 功能特点

- 从规则书自动提取问答对（带示例的规则、关键词效果、效果时机等）
- 预留官方 Q&A 上传接口（支持爬虫数据导入）
- 支持多种数据格式（instruction、conversation）
- 4-bit/8-bit 量化训练（QLoRA）
- 完整的训练监控和日志

## 环境准备

```bash
cd card_game_judge/finetune
pip install -r requirements.txt
```

> Windows 用户安装 `bitsandbytes` 可能需要特殊处理：
> https://github.com/jllllll/bitsandbytes-windows-webui

## 使用步骤

### 1. 收集训练数据

```bash
# 从规则书提取问答对
python data_collector.py

# 创建 Q&A 模板文件
python data_collector.py --create-template

# 指定规则书路径
python data_collector.py --rulebook ../数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt

# 加载官方 Q&A
python data_collector.py --qa-file training_data/official_qa.json
```

### 2. 添加官方 Q&A（可选）

编辑 `training_data/official_qa.json`：

```json
[
  {
    "question": "问题内容",
    "answer": "答案内容",
    "card_no": "BT01-001",
    "card_name": "卡牌名称",
    "source": "官方网站",
    "date": "2025-01-01"
  }
]
```

### 3. 开始微调

```bash
# 使用默认配置（Qwen2-1.5B）
python finetune_qwen.py

# 使用 7B 模型
python finetune_qwen.py --model Qwen/Qwen2-7B-Instruct

# 自定义参数
python finetune_qwen.py \
    --model Qwen/Qwen2-1.5B-Instruct \
    --data training_data/dtcg_finetune_data.jsonl \
    --output output/my_model \
    --epochs 5 \
    --batch_size 4 \
    --lora_r 32

# 训练后合并权重
python finetune_qwen.py --merge
```

### 4. 使用微调后的模型

```python
from finetune_qwen import DTCGFineTuner

# 加载微调后的模型
model, tokenizer = DTCGFineTuner.load_finetuned("output/dtcg_qwen_lora")

# 推理
prompt = """<|im_start|>system
你是数码宝贝卡牌游戏(DTCG)的规则专家。<|im_end|>
<|im_start|>user
≪贯通≫效果如何处理？<|im_end|>
<|im_start|>assistant
"""
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 数据格式

### instruction 格式（默认）

```json
{
  "instruction": "你是数码宝贝卡牌游戏(DTCG)的规则专家。",
  "input": "≪贯通≫是什么效果？",
  "output": "≪贯通≫是..."
}
```

### conversation 格式

```json
{
  "conversations": [
    {"role": "system", "content": "你是DTCG规则专家。"},
    {"role": "user", "content": "≪贯通≫是什么效果？"},
    {"role": "assistant", "content": "≪贯通≫是..."}
  ]
}
```

## 显存需求

| 模型 | 4-bit 量化 | 显存需求 |
|------|-----------|---------|
| Qwen2-1.5B | 是 | ~6GB |
| Qwen2-1.5B | 否 | ~12GB |
| Qwen2-7B | 是 | ~12GB |
| Qwen2-7B | 否 | ~28GB |

## 文件说明

```
finetune/
├── data_collector.py      # 数据收集脚本
├── finetune_qwen.py       # LoRA 微调脚本
├── requirements.txt       # 依赖列表
├── README.md              # 说明文档
├── training_data/         # 训练数据目录
│   ├── official_qa.json   # 官方 Q&A（需手动添加或爬取）
│   ├── dtcg_finetune_data.jsonl  # 生成的训练数据
│   └── dtcg_conversation.jsonl   # 对话格式数据
└── output/                # 模型输出目录
    └── dtcg_qwen_lora/    # LoRA 权重
```

## 官方 Q&A 爬虫接口

`data_collector.py` 预留了 Q&A 上传接口，可以通过以下方式导入爬取的数据：

```python
from data_collector import DTCGDataCollector

collector = DTCGDataCollector()

# 方式1: 直接添加
qa_list = [
    {"question": "...", "answer": "...", "card_no": "BT01-001"},
    # ...
]
collector.add_official_qa(qa_list)

# 方式2: 批量上传（供爬虫使用）
collector.upload_qa_batch(qa_data)

# 方式3: 从文件加载
collector.load_official_qa_from_file("official_qa.json")

# 导出
collector.export_jsonl()
```

## 训练建议

1. **数据量**: 建议至少 500+ 条高质量问答对
2. **训练轮数**: 3-5 轮通常足够，过多可能过拟合
3. **学习率**: 2e-4 是个好的起点，可根据 loss 调整
4. **LoRA rank**: 32-64 对于规则问答任务足够
