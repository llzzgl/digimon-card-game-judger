# 使用微调模型指南

## 🎉 恭喜微调成功！

现在你可以在项目中使用微调后的模型了。

---

## 📁 文件结构

```
card_game_judge/
├── finetune/
│   └── output/
│       └── dtcg_qwen_lora/          # 你的微调模型（LoRA 适配器）
│           ├── adapter_config.json
│           ├── adapter_model.bin
│           └── ...
│
├── app/
│   ├── llm_service.py               # 主 LLM 服务（已更新）
│   └── llm_service_finetuned.py     # 微调模型服务（新增）
│
└── .env                             # 配置文件（已更新）
```

---

## 🚀 使用方法

### 前置要求

使用微调模型需要安装额外的依赖：

```bash
# Windows
install_finetuned_deps.bat

# Linux/Mac
chmod +x install_finetuned_deps.sh
./install_finetuned_deps.sh

# 或手动安装
pip install peft transformers accelerate bitsandbytes torch
```

---

### 方法 1：修改 .env 文件（推荐）

编辑 `card_game_judge/.env` 文件：

```bash
# 将 LLM_MODEL 改为 finetuned
LLM_MODEL=finetuned

# 配置微调模型路径（默认值通常不需要修改）
FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct
```

### 方法 2：环境变量

```bash
export LLM_MODEL=finetuned
export FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
export FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct

python main.py
```

---

## 🔄 切换模型

你可以随时在不同模型之间切换：

```bash
# 使用微调模型
LLM_MODEL=finetuned

# 使用通义千问 API
LLM_MODEL=qwen

# 使用 Gemini API
LLM_MODEL=gemini

# 使用本地 Ollama
LLM_MODEL=local

# 使用 OpenAI API
LLM_MODEL=openai
```

---

## 📊 模型对比

| 模型 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **finetuned** | • 专门针对 DTCG 训练<br>• 本地运行，无需 API<br>• 免费使用 | • 需要 GPU<br>• 首次加载较慢<br>• 占用显存 | 生产环境，需要最佳效果 |
| **qwen** | • 速度快<br>• 稳定可靠 | • 需要 API Key<br>• 有费用 | 开发测试 |
| **gemini** | • 免费额度大<br>• 效果好 | • 需要代理<br>• 可能不稳定 | 临时使用 |
| **local** | • 完全本地<br>• 免费 | • 需要安装 Ollama<br>• 通用模型 | 离线环境 |

---

## ⚙️ 配置说明

### FINETUNED_LORA_PATH

LoRA 适配器的路径，相对于项目根目录。

**默认值：** `finetune/output/dtcg_qwen_lora`

**如果你的模型在其他位置：**
```bash
# 绝对路径
FINETUNED_LORA_PATH=/path/to/your/lora

# 相对路径
FINETUNED_LORA_PATH=finetune/output/my_custom_lora
```

### FINETUNED_BASE_MODEL

基础模型名称，用于加载 tokenizer 和基础权重。

**可选值：**
- `Qwen/Qwen2-1.5B-Instruct` （默认，推荐）
- `Qwen/Qwen2-7B-Instruct` （如果你用 7B 模型微调）
- `Qwen/Qwen2-0.5B-Instruct` （如果你用 0.5B 模型微调）

---

## 🔍 验证模型加载

启动项目后，查看日志：

```bash
python main.py
```

应该看到：

```
🎯 使用微调后的 Qwen2 模型
📥 加载微调模型...
   基础模型: Qwen/Qwen2-1.5B-Instruct
   LoRA 路径: finetune/output/dtcg_qwen_lora
✅ 模型加载完成，设备: cuda
```

---

## 💡 性能优化

### 1. 使用 GPU

确保 PyTorch 可以使用 GPU：

```python
import torch
print(torch.cuda.is_available())  # 应该返回 True
```

### 2. 调整生成参数

编辑 `app/llm_service_finetuned.py`：

```python
class FinetunedQwenLLM(LLM):
    max_length: int = 2048        # 输入最大长度
    temperature: float = 0.1      # 温度（越低越确定）
    top_p: float = 0.9            # 采样参数
```

### 3. 减少显存占用

如果显存不足，可以使用量化：

```python
# 在 llm_service_finetuned.py 的 _load_model 方法中
base_model_obj = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.float16,     # 使用 float16
    device_map="auto",
    trust_remote_code=True,
    load_in_8bit=True              # 添加 8-bit 量化
)
```

---

## 🐛 常见问题

### Q1: 模型加载失败

**错误：** `FileNotFoundError: finetune/output/dtcg_qwen_lora`

**解决：** 检查路径是否正确，确保 LoRA 文件存在：

```bash
ls finetune/output/dtcg_qwen_lora/
# 应该看到：adapter_config.json, adapter_model.bin 等文件
```

### Q2: 显存不足

**错误：** `CUDA out of memory`

**解决方案：**
1. 使用更小的基础模型（0.5B 或 1.5B）
2. 启用 8-bit 量化
3. 减小 `max_length` 参数

### Q3: 生成速度慢

**原因：** 首次加载模型需要时间

**解决：**
- 模型会缓存在内存中，后续请求会很快
- 考虑使用更小的模型
- 确保使用 GPU

### Q4: 回答质量不理想

**可能原因：**
1. 训练数据不足
2. 训练轮数太少
3. 学习率不合适

**解决：**
- 收集更多训练数据
- 增加训练轮数（3-5 轮）
- 调整微调参数重新训练

---

## 📈 效果评估

### 测试微调效果

创建测试脚本 `test_finetuned.py`：

```python
from app.llm_service_finetuned import get_finetuned_llm_service

# 初始化服务
service = get_finetuned_llm_service()

# 测试问题
test_cases = [
    {
        "question": "EX11-026 是什么卡？",
        "context": []
    },
    {
        "question": "≪贯通≫效果如何处理？",
        "context": []
    }
]

for case in test_cases:
    print(f"\n问题: {case['question']}")
    answer = service.generate_answer(case['question'], case['context'])
    print(f"回答: {answer}")
```

---

## 🔄 更新模型

如果你重新训练了模型：

1. **替换 LoRA 文件：**
   ```bash
   rm -rf finetune/output/dtcg_qwen_lora
   cp -r finetune/output/new_lora finetune/output/dtcg_qwen_lora
   ```

2. **重启服务：**
   ```bash
   # 停止当前服务
   # 重新启动
   python main.py
   ```

3. **模型会自动重新加载**

---

## 📝 最佳实践

### 1. 开发环境

开发时使用 API 模型（qwen/gemini），速度快，方便调试：

```bash
LLM_MODEL=qwen
```

### 2. 生产环境

部署时使用微调模型，效果最好：

```bash
LLM_MODEL=finetuned
```

### 3. 备用方案

配置多个模型，出问题时可以快速切换：

```bash
# 主模型
LLM_MODEL=finetuned

# 如果微调模型有问题，改为：
LLM_MODEL=qwen
```

---

## 🎯 下一步

1. **测试效果**：用实际问题测试微调模型的回答质量
2. **收集反馈**：记录哪些问题回答得好，哪些不好
3. **持续改进**：根据反馈调整训练数据，重新微调
4. **监控性能**：关注响应时间和显存占用

---

## 📞 技术支持

如有问题，请检查：
1. [QUICK_START.md](finetune/QUICK_START.md) - 微调快速开始
2. [COMPLETION_REPORT.md](finetune/COMPLETION_REPORT.md) - 微调完成报告
3. 项目日志输出

---

**最后更新：** 2026-01-26  
**版本：** v1.0
