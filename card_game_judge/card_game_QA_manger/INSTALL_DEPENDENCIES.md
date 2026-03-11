# 安装依赖指南

## 快速安装

如果你使用的是 `llm` conda环境，运行以下命令：

```bash
conda activate llm
pip install openai python-dotenv
```

如果需要使用Gemini：
```bash
pip install google-generativeai
```

## 详细说明

### 1. 激活conda环境

```bash
conda activate llm
```

### 2. 安装必需的库

#### 使用Qwen或Ollama

```bash
pip install openai
```

这个库提供了OpenAI兼容的API接口，Qwen和Ollama都使用这个接口。

#### 使用Gemini

```bash
pip install google-generativeai
```

#### 其他依赖

```bash
pip install python-dotenv
```

用于加载 `.env` 文件中的环境变量。

### 3. 验证安装

运行检查脚本：

```bash
python check_dependencies.py
```

这会显示：
- 哪些库已安装
- 哪些库缺失
- 各个LLM是否可用

## 完整依赖列表

| 库名 | 用途 | 安装命令 | 必需性 |
|------|------|----------|--------|
| openai | Qwen/Ollama API | `pip install openai` | Qwen/Ollama必需 |
| google-generativeai | Gemini API | `pip install google-generativeai` | Gemini必需 |
| python-dotenv | 环境变量加载 | `pip install python-dotenv` | 推荐 |
| json | JSON处理 | 内置 | 必需 |
| pathlib | 路径处理 | 内置 | 必需 |

## 版本要求

- Python >= 3.8
- openai >= 1.0.0 (推荐最新版)
- google-generativeai >= 0.3.0 (推荐最新版)

## 常见问题

### Q: pip install 很慢

A: 使用国内镜像源：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openai
```

### Q: 提示"No module named 'openai'"

A: 确保：
1. 已激活正确的conda环境
2. 已运行 `pip install openai`
3. 重启Python解释器或IDE

### Q: openai版本太旧

A: 更新到最新版：

```bash
pip install --upgrade openai
```

### Q: 安装google-generativeai失败

A: 尝试：

```bash
pip install --upgrade pip
pip install google-generativeai
```

## 一键安装脚本

创建 `install_deps.bat` (Windows):

```batch
@echo off
echo 安装翻译工具依赖...
conda activate llm
pip install openai python-dotenv
pip install google-generativeai
echo 安装完成！
pause
```

创建 `install_deps.sh` (Linux/Mac):

```bash
#!/bin/bash
echo "安装翻译工具依赖..."
conda activate llm
pip install openai python-dotenv
pip install google-generativeai
echo "安装完成！"
```

## 验证安装成功

运行以下Python代码：

```python
# 测试openai
try:
    import openai
    print(f"✓ openai {openai.__version__}")
except ImportError:
    print("✗ openai 未安装")

# 测试google-generativeai
try:
    import google.generativeai as genai
    print("✓ google-generativeai")
except ImportError:
    print("✗ google-generativeai 未安装")

# 测试python-dotenv
try:
    import dotenv
    print("✓ python-dotenv")
except ImportError:
    print("✗ python-dotenv 未安装")
```

或者直接运行：

```bash
python check_dependencies.py
```
