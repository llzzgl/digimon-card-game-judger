"""
LLM配置文件
可以在这里修改使用的LLM类型和模型
"""

# LLM类型选择: "qwen", "gemini", "openai"
LLM_TYPE = "qwen"

# 模型配置
MODEL_CONFIG = {
    "qwen": {
        "model": "qwen-plus",  # 可选: "qwen-turbo", "qwen-plus", "qwen-max"
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "gemini": {
        "model": "gemini-2.0-flash-exp",  # 可选: "gemini-pro", "gemini-2.0-flash-exp"
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "openai": {
        "model": "gpt-4o-mini",  # 可选: "gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"
        "temperature": 0.3,
        "max_tokens": 2000,
    }
}

# 提取参数
EXTRACTION_CONFIG = {
    "sample_size": 10000,   # 设置为一个很大的数字，实际会收集所有可用样本
    "batch_size": 20,       # 增大批次以提高效率
    "enable_refine": True,  # 是否启用精炼和分类
}

# API配置（从.env文件读取）
# DASHSCOPE_API_KEY - 通义千问
# GOOGLE_API_KEY 或 GEMINI_API_KEY - Gemini
# OPENAI_API_KEY - OpenAI
