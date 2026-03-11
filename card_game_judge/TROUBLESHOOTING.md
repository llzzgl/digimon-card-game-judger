# 故障排除指南

## ❌ 错误：HTTP 502 Bad Gateway

### 症状
- 浏览器显示 "该网页无法正常运作"
- 错误代码：HTTP ERROR 502
- 服务无法访问

### 原因
服务启动失败，通常是因为：
1. 模型加载失败
2. 依赖库缺失
3. 配置错误

---

## 🔍 诊断步骤

### 步骤 1：运行诊断工具

```bash
python diagnose.py
```

这会自动检查：
- ✅ 环境配置
- ✅ 依赖库
- ✅ 模型加载
- ✅ API 模块

---

## ✅ 快速解决方案

### 方案 1：使用 API 模型（最快）⭐

**适用场景：** 需要立即使用，不想处理模型加载问题

```bash
# Windows
start_with_api.bat

# Linux/Mac
export LLM_MODEL=qwen
python main.py
```

**或修改 .env：**
```bash
LLM_MODEL=qwen
```

---

### 方案 2：合并微调模型

**适用场景：** 想使用微调模型，但遇到加载问题

```bash
# 1. 合并 LoRA 权重
python merge_lora.py

# 2. 修改 .env
FINETUNED_BASE_MODEL=finetune/output/dtcg_qwen_merged
FINETUNED_LORA_PATH=

# 3. 重新启动
python main.py
```

---

### 方案 3：安装缺失依赖

**适用场景：** 诊断工具提示依赖缺失

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或只安装微调模型依赖
pip install peft transformers accelerate bitsandbytes torch
```

---

## 🐛 常见问题

### Q1: 模型加载超时

**症状：** 启动时卡住很久，最后失败

**原因：** 首次下载模型需要时间

**解决：**
1. 检查网络连接
2. 使用代理（如果需要）
3. 或使用已下载的模型

---

### Q2: 显存不足

**症状：** `CUDA out of memory`

**解决：**
```bash
# 方案 1: 使用更小的模型
FINETUNED_BASE_MODEL=Qwen/Qwen2-0.5B-Instruct

# 方案 2: 使用 CPU
export CUDA_VISIBLE_DEVICES=""

# 方案 3: 使用 API 模型
LLM_MODEL=qwen
```

---

### Q3: 端口被占用

**症状：** `Address already in use`

**解决：**
```bash
# 使用其他端口
python main.py --port 8001

# 或关闭占用端口的程序
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000
```

---

### Q4: 依赖版本冲突

**症状：** 各种 ImportError 或 AttributeError

**解决：**
```bash
# 创建新的虚拟环境
conda create -n dtcg python=3.9
conda activate dtcg

# 重新安装依赖
pip install -r requirements.txt
```

---

## 📋 完整诊断流程

### 1. 运行诊断
```bash
python diagnose.py
```

### 2. 查看输出

**如果看到：**
```
✅ 所有检查通过！
```
→ 直接启动：`python main.py`

**如果看到：**
```
❌ 微调模型加载失败
```
→ 运行：`python merge_lora.py` 或切换到 API 模型

**如果看到：**
```
❌ 依赖库未安装
```
→ 运行：`pip install -r requirements.txt`

### 3. 重新启动
```bash
python main.py
```

---

## 🎯 推荐配置

### 开发/测试环境
```bash
# .env
LLM_MODEL=qwen  # 快速稳定
```

### 生产环境
```bash
# .env
LLM_MODEL=finetuned
FINETUNED_BASE_MODEL=finetune/output/dtcg_qwen_merged  # 合并后的模型
FINETUNED_LORA_PATH=  # 留空
```

---

## 📊 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 快速测试 | qwen | 稳定快速 |
| 开发调试 | qwen | 无需本地模型 |
| 生产部署 | finetuned (merged) | 效果最好 |
| 离线环境 | finetuned (merged) | 不需要网络 |
| 显存不足 | qwen | 无需显存 |

---

## 🔧 启动脚本对比

| 脚本 | 模型 | 适用场景 |
|------|------|----------|
| `python main.py` | 按 .env 配置 | 正常启动 |
| `start_with_api.bat` | API 模型 | 快速稳定 ⭐ |
| `start_with_finetuned.bat` | 微调模型 | 最佳效果 |
| `fix_and_start.bat` | 自动修复 | 有问题时 |

---

## 📞 获取帮助

### 1. 查看日志
启动时的完整输出可以帮助定位问题

### 2. 运行诊断
```bash
python diagnose.py
```

### 3. 查看文档
- [QUICK_FIX.md](QUICK_FIX.md) - 快速修复
- [FIX_LORA_LOADING.md](FIX_LORA_LOADING.md) - LoRA 加载问题
- [USE_FINETUNED_MODEL.md](USE_FINETUNED_MODEL.md) - 微调模型使用

---

## ✅ 验证服务正常

启动后应该看到：

```
🎴 卡牌游戏智能裁判
🌐 打开浏览器访问: http://localhost:8000
📖 API 文档: http://localhost:8000/docs
⏳ 首次启动需要加载模型，请稍候...
✅ [卡牌数据] 加载中文卡牌数据成功: 3992 张
🎯 使用微调后的 Qwen2 模型  # 或其他模型
✅ 模型加载完成
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

然后访问 http://localhost:8000 应该能看到界面。

---

**最后更新：** 2026-01-26  
**推荐方案：** 先用 API 模型测试，确认服务正常后再切换微调模型
