# 模型配置修复说明

## 问题

之前的配置使用了错误的API端点和模型名称组合：
- ❌ base_url: `https://coding.dashscope.aliyuncs.com/v1` + model: `qwen3.5-plus`
- ❌ base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1` + model: `qwen-plus`

导致错误：`model 'qwen-plus' is not supported`

## 解决方案

统一使用OpenAI兼容接口：
- ✅ base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- ✅ model: `qwen-turbo` (稳定、快速、支持良好)

## 可用的模型

在OpenAI兼容接口下，支持以下模型：

| 模型名称 | 速度 | 质量 | 成本 | 推荐场景 |
|---------|------|------|------|----------|
| qwen-turbo | 快 | 中 | 低 | 日常翻译（推荐） |
| qwen-plus | 中 | 高 | 中 | 高质量翻译 |
| qwen-max | 慢 | 最高 | 高 | 重要文档 |
| qwen-long | 中 | 高 | 中 | 长文本处理 |

## 修改的文件

1. `translate_qa_with_terminology.py`
   - 修改 base_url
   - 修改 model_name 为 `qwen-turbo`

2. `test_qwen_api.py`
   - 统一使用 `qwen-turbo`

## 现在可以使用

```bash
# 测试API
python test_qwen_api.py

# 翻译QA
python translate_qa_with_terminology.py
```

应该可以正常工作了！

## 如果需要更高质量

修改 `translate_qa_with_terminology.py` 第73行：

```python
self.model_name = "qwen-plus"  # 或 "qwen-max"
```

## 参考文档

- [通义千问OpenAI兼容文档](https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope)
- [模型列表](https://help.aliyun.com/zh/dashscope/developer-reference/model-square)
