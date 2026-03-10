# 翻译问题排查指南

## 问题：程序卡在 [1/10] 不动

### 可能原因

1. **API连接超时** - 网络问题或API服务器响应慢
2. **API密钥错误** - 密钥无效或过期
3. **提示词太长** - 超过模型的token限制
4. **API限流** - 请求过于频繁

### 诊断步骤

#### 步骤1: 测试API连接

```bash
python test_qwen_api.py
```

这会测试：
- ✓ API密钥是否正确加载
- ✓ 能否连接到通义千问服务器
- ✓ 简单的API调用是否成功
- ✓ 翻译任务是否能正常工作

**预期输出**:
```
✓ .env文件已加载
✓ API密钥已加载: sk-xxxxx...xxxx
✓ 客户端初始化成功
✓ API响应: OK
✓ 翻译结果: 这张卡的【登场时】效果，可以休眠自己的数码兽吗？
✓ 所有测试通过！API连接正常
```

**如果失败**:
- 检查网络连接
- 检查API密钥是否正确
- 检查是否需要代理

#### 步骤2: 翻译单条QA

```bash
python translate_single_qa.py
```

这会：
- 加载一条QA
- 显示提示词信息
- 尝试翻译
- 显示详细的错误信息

**预期输出**:
```
✓ 初始化翻译器
提示词长度: 3500 字符
术语数量: 79
卡牌数量: 3992
✓ 翻译完成
```

**如果失败**:
- 查看具体错误信息
- 检查提示词是否太长
- 检查术语表是否正确加载

#### 步骤3: 一键诊断

```bash
diagnose_translation.bat
```

这会自动运行步骤1和步骤2。

## 常见问题和解决方案

### 1. API连接超时

**症状**: 程序卡住不动，或提示 "timeout"

**解决方案**:
```python
# 在 translate_qa_with_terminology.py 中
# 已添加 timeout=60 参数
# 如果还是超时，可以增加到 120
```

或者检查网络：
```bash
ping dashscope.aliyuncs.com
```

### 2. API密钥错误

**症状**: 提示 "invalid api key" 或 "authentication failed"

**解决方案**:
1. 检查 `.env` 文件中的密钥
2. 确认密钥格式正确（sk-开头）
3. 登录阿里云控制台确认密钥有效

### 3. 提示词太长

**症状**: 提示 "token limit exceeded" 或程序卡住

**解决方案**:

减少提示词中的术语数量：
```python
# 在 _build_translation_prompt 方法中
# 将 100 改为 50
for jp, cn_list in self.terminology.items():
    if count >= 50:  # 从100改为50
        break
```

或使用更大的模型：
```python
self.model_name = "qwen-max"  # 支持更长的上下文
```

### 4. API限流

**症状**: 提示 "rate limit exceeded" 或 "too many requests"

**解决方案**:

增加延迟：
```python
translator.translate_all(
    batch_size=5,   # 减小批次
    delay=2.0       # 增加延迟到2秒
)
```

### 5. 内存不足

**症状**: 程序崩溃或提示 "out of memory"

**解决方案**:

减小批次大小：
```python
translator.translate_all(
    batch_size=5,   # 从10改为5
    delay=1.0
)
```

## 调试技巧

### 1. 查看详细日志

程序现在会显示：
```
[1/10] QA#5794 [问题] [提示词: 3500字符] 调用Qwen API... 完成 [答案] ...
```

如果卡住，看看卡在哪个步骤：
- 卡在 "调用Qwen API..." → API连接问题
- 卡在 "[问题]" 之前 → 数据加载问题
- 卡在 "[答案]" 之前 → 问题翻译成功，答案翻译卡住

### 2. 使用Ctrl+C中断

如果程序卡住，按 Ctrl+C 中断。程序会：
- 保存已翻译的内容
- 创建检查点文件
- 下次运行时从断点继续

### 3. 检查检查点文件

```bash
dir official_qa_cn_*_checkpoint.json
```

如果存在，说明之前的翻译被中断了。可以：
- 继续翻译（自动从断点开始）
- 或删除检查点重新开始

### 4. 查看Python错误

如果有Python错误，会显示完整的traceback。常见错误：

**ImportError**: 缺少依赖
```bash
pip install openai python-dotenv
```

**FileNotFoundError**: 文件路径错误
- 检查工作目录
- 检查文件是否存在

**KeyError**: 数据格式错误
- 检查JSON文件格式
- 检查必需字段是否存在

## 临时解决方案

如果问题无法立即解决，可以：

### 1. 使用更简单的提示词

创建 `translate_simple.py`，使用最简单的提示词：
```python
prompt = "请将以下日文完整翻译成中文：\n\n" + text
```

### 2. 使用其他LLM

尝试 Gemini 或 Ollama：
```bash
python translate_qa_with_terminology.py
# 选择 2 (Gemini) 或 3 (Ollama)
```

### 3. 分批翻译

不要一次翻译全部，分批进行：
```python
# 第一批：0-100
translator.translate_all(start_from=0, max_count=100)

# 第二批：100-200
translator.translate_all(start_from=100, max_count=100)
```

### 4. 使用在线翻译API

如果Qwen不稳定，可以考虑：
- 百度翻译API
- 腾讯翻译API
- DeepL API

## 获取帮助

如果以上方法都无法解决，请提供：

1. **test_qwen_api.py 的完整输出**
2. **translate_single_qa.py 的完整输出**
3. **错误信息的完整traceback**
4. **Python版本**: `python --version`
5. **依赖版本**: `pip list | grep openai`

## 快速检查清单

- [ ] 运行 `python test_qwen_api.py` 成功
- [ ] 运行 `python translate_single_qa.py` 成功
- [ ] API密钥正确配置
- [ ] 网络连接正常
- [ ] 依赖库已安装
- [ ] 数据文件存在
- [ ] 有足够的磁盘空间

如果所有项都打勾，但还是有问题，可能是：
- 通义千问服务器临时故障
- 账户配额用完
- 防火墙阻止连接

## 联系支持

- 通义千问技术支持: https://help.aliyun.com/
- 查看API状态: https://status.aliyun.com/
