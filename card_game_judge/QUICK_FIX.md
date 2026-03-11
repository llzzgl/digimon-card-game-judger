# 快速修复指南

## ❌ 错误：ModuleNotFoundError: No module named 'peft'

### 原因
使用微调模型需要额外的依赖库，但当前环境中没有安装。

---

## ✅ 解决方案

### 方案 1：安装依赖（推荐）

**Windows:**
```bash
install_finetuned_deps.bat
```

**Linux/Mac:**
```bash
chmod +x install_finetuned_deps.sh
./install_finetuned_deps.sh
```

**手动安装:**
```bash
pip install peft transformers accelerate bitsandbytes torch
```

安装完成后重新启动：
```bash
python main.py
```

---

### 方案 2：暂时使用 API 模型

如果不想安装依赖，可以先使用 API 模型：

编辑 `.env` 文件：
```bash
# 改为使用通义千问 API
LLM_MODEL=qwen

# 或使用 Gemini API
LLM_MODEL=gemini
```

然后启动：
```bash
python main.py
```

---

## 📦 完整依赖列表

使用微调模型需要以下库：

| 库 | 版本 | 用途 |
|---|---|---|
| peft | >=0.7.0 | LoRA 适配器加载 |
| transformers | >=4.36.0 | 模型加载和推理 |
| accelerate | >=0.25.0 | 模型加速 |
| bitsandbytes | >=0.41.0 | 量化支持 |
| torch | >=2.0.0 | PyTorch 框架 |

---

## 🔍 验证安装

安装完成后，验证是否成功：

```python
python -c "import peft; import transformers; print('✅ 依赖安装成功！')"
```

应该看到：
```
✅ 依赖安装成功！
```

---

## 🚀 启动服务

依赖安装完成后：

```bash
# 确认使用微调模型
# 编辑 .env: LLM_MODEL=finetuned

# 启动服务
python main.py

# 或使用快捷脚本
start_with_finetuned.bat  # Windows
./start_with_finetuned.sh # Linux/Mac
```

---

## 💡 其他常见错误

### 错误 1: CUDA out of memory
**解决：** 使用更小的模型或启用量化

### 错误 2: No module named 'torch'
**解决：** `pip install torch`

### 错误 3: 模型加载失败
**解决：** 检查 LoRA 文件是否存在
```bash
ls finetune/output/dtcg_qwen_lora/
```

---

## 📞 需要帮助？

查看详细文档：
- [USE_FINETUNED_MODEL.md](USE_FINETUNED_MODEL.md) - 完整使用指南
- [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - 集成说明

---

**最后更新：** 2026-01-26
