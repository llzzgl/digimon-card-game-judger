# 修复 LoRA 加载问题

## ❌ 错误信息

```
KeyError: 'base_model.model.model.model.embed_tokens'
```

## 🔍 问题原因

这是 PEFT 库加载 LoRA 适配器时的兼容性问题，通常由以下原因引起：
1. PEFT 版本与训练时使用的版本不同
2. 模型结构与 LoRA 适配器不匹配
3. `device_map="auto"` 导致的模块命名问题

---

## ✅ 解决方案

### 方案 1：合并 LoRA 权重（推荐）⭐

将 LoRA 权重合并到基础模型中，避免加载时的兼容性问题。

**步骤：**

```bash
# 1. 运行合并脚本
python merge_lora.py

# 2. 修改 .env 文件
# 将 FINETUNED_BASE_MODEL 改为合并后的模型路径
FINETUNED_BASE_MODEL=finetune/output/dtcg_qwen_merged
FINETUNED_LORA_PATH=  # 留空

# 3. 重新启动
python main.py
```

**优点：**
- ✅ 避免兼容性问题
- ✅ 加载速度更快
- ✅ 不需要 PEFT 库

---

### 方案 2：更新 PEFT 版本

```bash
# 卸载旧版本
pip uninstall peft -y

# 安装最新版本
pip install peft --upgrade

# 重新启动
python main.py
```

---

### 方案 3：使用 API 模型（临时）

如果急需使用，可以先切换到 API 模型：

编辑 `.env`：
```bash
LLM_MODEL=qwen  # 或 gemini
```

---

## 📝 详细步骤：合并 LoRA 权重

### 步骤 1：运行合并脚本

```bash
python merge_lora.py
```

你会看到：
```
============================================================
合并 LoRA 权重到基础模型
============================================================

基础模型: Qwen/Qwen2-1.5B-Instruct
LoRA 路径: finetune/output/dtcg_qwen_lora
输出路径: finetune/output/dtcg_qwen_merged

📥 步骤 1/4: 加载基础模型...
✅ 基础模型加载完成

📥 步骤 2/4: 加载 LoRA 适配器...
✅ LoRA 适配器加载完成

🔄 步骤 3/4: 合并权重...
✅ 权重合并完成

💾 步骤 4/4: 保存到 finetune/output/dtcg_qwen_merged...
✅ 模型保存完成

============================================================
✅ 合并完成！
============================================================
```

### 步骤 2：修改配置

编辑 `.env` 文件：

**之前：**
```bash
LLM_MODEL=finetuned
FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct
```

**之后：**
```bash
LLM_MODEL=finetuned
FINETUNED_BASE_MODEL=finetune/output/dtcg_qwen_merged
FINETUNED_LORA_PATH=  # 留空或删除这行
```

### 步骤 3：重新启动

```bash
python main.py
```

应该看到：
```
🎯 使用微调后的 Qwen2 模型
📥 加载微调模型...
   基础模型: finetune/output/dtcg_qwen_merged
   LoRA 路径: 
   检测到合并模型，直接加载...
✅ 模型加载完成，设备: cuda
```

---

## 🔧 自定义合并参数

如果需要自定义合并参数：

```bash
python merge_lora.py \
    --lora-path finetune/output/dtcg_qwen_lora \
    --base-model Qwen/Qwen2-1.5B-Instruct \
    --output finetune/output/my_merged_model
```

---

## 📊 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **合并权重** | 兼容性好，加载快 | 需要额外存储空间 | ⭐⭐⭐⭐⭐ |
| **更新 PEFT** | 保持原有结构 | 可能仍有问题 | ⭐⭐⭐ |
| **使用 API** | 快速解决 | 需要 API Key | ⭐⭐ |

---

## 💾 存储空间说明

### LoRA 模式
```
finetune/output/
└── dtcg_qwen_lora/          # ~100 MB
    ├── adapter_config.json
    └── adapter_model.bin
```

### 合并模式
```
finetune/output/
├── dtcg_qwen_lora/          # ~100 MB (可保留作备份)
└── dtcg_qwen_merged/        # ~3 GB (完整模型)
    ├── config.json
    ├── model.safetensors
    └── tokenizer files
```

**建议：**
- 如果存储空间充足，使用合并模式（推荐）
- 如果存储空间有限，尝试更新 PEFT 版本

---

## 🐛 其他常见问题

### Q1: 合并时显存不足
**解决：** 使用 CPU 合并
```bash
export CUDA_VISIBLE_DEVICES=""  # 禁用 GPU
python merge_lora.py
```

### Q2: 合并后模型太大
**解决：** 使用更小的基础模型
```bash
python merge_lora.py --base-model Qwen/Qwen2-0.5B-Instruct
```

### Q3: 找不到 LoRA 文件
**解决：** 检查路径
```bash
ls finetune/output/dtcg_qwen_lora/
# 应该看到 adapter_config.json 和 adapter_model.bin
```

---

## 📞 需要帮助？

查看相关文档：
- [QUICK_FIX.md](QUICK_FIX.md) - 快速修复指南
- [USE_FINETUNED_MODEL.md](USE_FINETUNED_MODEL.md) - 使用指南
- [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - 集成说明

---

**最后更新：** 2026-01-26  
**推荐方案：** 合并 LoRA 权重 ⭐
