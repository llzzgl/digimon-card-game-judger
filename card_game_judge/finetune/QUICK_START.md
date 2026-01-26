# 快速开始 - DTCG 微调

## 📁 准备工作

### 确认源数据文件

确保 `origin_data/` 文件夹中包含以下文件：

```
origin_data/
├── rulebook.txt        # 规则书文件
├── cards.json          # 卡牌数据文件
└── official_qa.json    # 官方 Q&A 文件
```

如果缺少文件，请参考 [origin_data/README.md](origin_data/README.md) 了解如何准备数据。

---

## 一键收集数据并开始微调

### 步骤 1：收集训练数据

```bash
cd card_game_judge/finetune
python collect_all_data.py
```

**输出示例：**
```
============================================================
DTCG 微调数据完整收集
============================================================

【步骤 1】从规则书提取问答...
✅ 从规则书提取了 XXX 条问答

【步骤 2】加载官方 Q&A...
✅ 加载了 XXX 条官方 Q&A

【步骤 3】加载卡牌数据...
✅ 从卡牌数据生成了 17,656 条问答

📊 总计生成 17,658 条训练数据
   • 规则书问答: 0
   • 官方 Q&A: 2
   • 卡牌数据问答: 17,656
   • 自定义问答: 0

📁 输出文件:
   • training_data\dtcg_finetune_data.jsonl
   • training_data\dtcg_finetune_data.json
   • training_data\dtcg_conversation.jsonl
```

### 步骤 2：开始微调

```bash
# 使用默认参数（Qwen2-1.5B）
python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl

# 或使用更大的模型（推荐）
python finetune_qwen.py \
    --model Qwen/Qwen2-7B-Instruct \
    --data training_data/dtcg_finetune_data.jsonl \
    --epochs 3 \
    --batch_size 2 \
    --output output/dtcg_qwen_7b_lora
```

### 步骤 3：等待训练完成

训练时间取决于：
- 模型大小（1.5B vs 7B）
- GPU 性能
- 数据量（17,658 条）
- 训练轮数

**预计时间：**
- Qwen2-1.5B + RTX 3090: ~2-3 小时
- Qwen2-7B + RTX 3090: ~6-8 小时

### 步骤 4：测试微调后的模型

```python
from finetune_qwen import DTCGFineTuner

# 加载微调后的模型
model, tokenizer = DTCGFineTuner.load_finetuned(
    lora_path="output/dtcg_qwen_lora",
    base_model="Qwen/Qwen2-1.5B-Instruct"
)

# 测试查询
prompt = "EX11-026 是什么卡？"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_length=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## 常见问题

### Q1: 内存不足怎么办？

**方案 1：减小 batch size**
```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --batch_size 1 \
    --gradient_accumulation_steps 16
```

**方案 2：使用更小的模型**
```bash
python finetune_qwen.py \
    --model Qwen/Qwen2-0.5B-Instruct \
    --data training_data/dtcg_finetune_data.jsonl
```

**方案 3：启用梯度检查点（默认已启用）**
```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --use_4bit  # 默认启用
```

### Q2: 如何只使用卡牌数据训练？

```bash
# 收集数据时跳过规则书
python collect_all_data.py --no-cards

# 或手动编辑 data_collector.py
```

### Q3: 如何添加自定义问答？

```python
from data_collector import DTCGDataCollector

collector = DTCGDataCollector()

# 添加自定义问答
collector.add_custom_qa(
    question="什么是数码合体？",
    answer="数码合体是一种特殊的登场方式...",
    tags=["规则", "数码合体"]
)

# 导出
collector.export_jsonl("custom_data.jsonl")
```

### Q4: 训练中断了怎么办？

微调脚本会自动保存检查点，可以从最后一个检查点继续训练：

```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --output output/dtcg_qwen_lora  # 使用相同的输出目录
```

### Q5: 如何合并 LoRA 权重？

```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --merge  # 训练完成后自动合并
```

或使用 Python：

```python
from finetune_qwen import DTCGFineTuner, FinetuneConfig

config = FinetuneConfig(output_dir="output/dtcg_qwen_lora")
trainer = DTCGFineTuner(config)
trainer.load_model()
trainer.merge_and_save("output/dtcg_qwen_merged")
```

## 高级配置

### 调整 LoRA 参数

```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --lora_r 128 \
    --lora_alpha 256 \
    --lora_dropout 0.1
```

### 调整学习率和训练轮数

```bash
python finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl \
    --epochs 5 \
    --learning_rate 1e-4
```

### 使用多 GPU 训练

```bash
# 使用 torchrun
torchrun --nproc_per_node=2 finetune_qwen.py \
    --data training_data/dtcg_finetune_data.jsonl
```

## 监控训练进度

训练日志会保存在 `output/dtcg_qwen_lora/runs/`，可以使用 TensorBoard 查看：

```bash
tensorboard --logdir output/dtcg_qwen_lora/runs
```

## 下一步

- 查看 [README_CARD_DATA.md](README_CARD_DATA.md) 了解卡牌数据集成详情
- 查看 [finetune_qwen.py](finetune_qwen.py) 了解微调脚本详情
- 查看 [data_collector.py](data_collector.py) 了解数据收集详情
