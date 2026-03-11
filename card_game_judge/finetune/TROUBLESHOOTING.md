# DTCG 微调训练故障排除指南

## 常见错误及解决方案

### 1. CUBLAS_STATUS_NOT_SUPPORTED 错误

**错误信息：**
```
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_SUPPORTED when calling `cublasLtMatmulAlgoGetHeuristic`
```

**原因：**
- bitsandbytes 4-bit 量化与某些 CUDA 版本或 GPU 架构不兼容
- 可能是 bitsandbytes 版本过旧

**解决方案（按优先级）：**

#### 方案 1：使用 8-bit 量化（推荐）
```bash
python finetune_qwen.py --use_8bit
```
8-bit 量化更稳定，兼容性更好。

#### 方案 2：更新 bitsandbytes
```bash
pip install --upgrade bitsandbytes
```

#### 方案 3：不使用量化（需要更多显存）
```bash
python finetune_qwen.py --no_quant --batch_size 1
```

#### 方案 4：检查 CUDA 兼容性
```bash
python check_cuda_env.py
```

### 2. 非法内存访问错误

**错误信息：**
```
Error an illegal memory access was encountered
```

**解决方案：**
- 已在代码中修复设备映射问题
- 确保使用最新版本的脚本
- 尝试降低 batch_size 和 max_length

### 3. CUDA Out of Memory (OOM)

**错误信息：**
```
RuntimeError: CUDA out of memory
```

**解决方案（逐步尝试）：**

1. 降低 batch_size：
```bash
python finetune_qwen.py --batch_size 1
```

2. 降低 max_length（修改配置文件）：
```python
max_length: int = 256  # 从 512 降到 256
```

3. 降低 LoRA rank：
```bash
python finetune_qwen.py --lora_r 32
```

4. 使用更激进的量化：
```bash
python finetune_qwen.py --use_8bit
```

5. 清理 GPU 缓存：
```python
import torch
torch.cuda.empty_cache()
```

### 4. 设备映射错误

**错误信息：**
```
ValueError: You can't train a model that has been loaded in 8-bit or 4-bit precision on a different device
```

**解决方案：**
- 已在代码中修复，使用 `device_map={"": torch.cuda.current_device()}`
- 确保使用最新版本的脚本

### 5. bitsandbytes 未安装或版本问题

**错误信息：**
```
ImportError: cannot import name 'BitsAndBytesConfig'
```

**解决方案：**
```bash
pip install bitsandbytes>=0.41.0
pip install transformers>=4.35.0
pip install peft>=0.6.0
pip install accelerate>=0.24.0
```

## 推荐配置

### 小显存 GPU（< 12GB）
```bash
python finetune_qwen.py \
    --use_8bit \
    --batch_size 1 \
    --lora_r 32
```

配置文件中设置：
```python
max_length: int = 256
gradient_accumulation_steps: int = 16
```

### 中等显存 GPU（12-24GB）
```bash
python finetune_qwen.py \
    --use_8bit \
    --batch_size 1 \
    --lora_r 64
```

配置文件中设置：
```python
max_length: int = 512
gradient_accumulation_steps: int = 16
```

### 大显存 GPU（> 24GB）
```bash
python finetune_qwen.py \
    --no_quant \
    --batch_size 2 \
    --lora_r 64
```

配置文件中设置：
```python
max_length: int = 1024
gradient_accumulation_steps: int = 8
```

## 环境检查

运行环境检查脚本：
```bash
python check_cuda_env.py
```

应该看到：
- ✅ CUDA 可用
- ✅ bitsandbytes 已安装
- ✅ PEFT 已安装
- ✅ Transformers 已安装
- ✅ CUDA 操作测试通过

## 版本要求

推荐的包版本：
```
torch>=2.0.0
transformers>=4.35.0
peft>=0.6.0
bitsandbytes>=0.41.0
accelerate>=0.24.0
datasets>=2.14.0
```

## 常见问题

### Q: 为什么默认使用 8-bit 而不是 4-bit？
A: 4-bit 量化在某些 GPU 架构和 CUDA 版本上有兼容性问题，8-bit 更稳定。

### Q: 训练速度太慢怎么办？
A: 
1. 增加 batch_size（如果显存允许）
2. 减少 gradient_accumulation_steps
3. 使用更小的 max_length
4. 考虑使用多 GPU 训练

### Q: 如何验证训练效果？
A: 查看 TensorBoard 日志：
```bash
tensorboard --logdir output/dtcg_qwen_lora
```

### Q: 训练中断后如何恢复？
A: Trainer 会自动保存检查点，重新运行训练脚本会从最后的检查点恢复。

## 联系支持

如果以上方案都无法解决问题，请提供：
1. 完整的错误堆栈信息
2. `check_cuda_env.py` 的输出
3. GPU 型号和显存大小
4. CUDA 版本
5. Python 包版本（`pip list | grep -E "torch|transformers|peft|bitsandbytes"`）
