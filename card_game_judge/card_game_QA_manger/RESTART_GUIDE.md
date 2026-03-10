# 重新开始翻译指南

## 问题说明

检查点文件显示索引错误（5851 > 4634），导致：
1. 无法继续翻译
2. 已翻译的55条中有7.3%仍有日文残留

## 解决方案

### 方法1: 一键重启（推荐）

```bash
restart_translation.bat
```

这会：
- 自动删除所有检查点
- 重新开始完整翻译
- 使用改进的提示词和自动模型切换

### 方法2: 手动清理

```bash
# 1. 删除检查点
del official_qa_cn_*_checkpoint.json

# 2. 重新翻译
python translate_qa_with_terminology.py
# 选择模式 3 (完整翻译)
```

### 方法3: 使用修复工具

```bash
python fix_checkpoint.py
```

选择选项1删除所有检查点。

## 翻译时间估算

- 总QA数量: 4634条
- 每条约需: 2-3秒
- 预计总时间: 2.5-4小时
- 批次间延迟: 1秒

建议：
- 在网络稳定时进行
- 可以随时Ctrl+C中断，会自动保存进度
- 下次运行会从断点继续

## 改进内容

新的翻译工具包含：

1. **更强的提示词**
   - 明确要求完全翻译成中文
   - 100个术语示例
   - 4个详细翻译示例

2. **自动模型切换**
   - qwen-turbo → qwen-plus → qwen-max → qwen-long
   - 配额用尽自动切换
   - 无需手动干预

3. **重试机制**
   - 每个模型重试3次
   - 指数退避策略
   - 网络错误自动恢复

4. **质量检查**
   - 运行后使用 `check_translation_quality.py` 检查
   - 自动检测日文残留
   - 统计翻译质量

## 开始翻译

```bash
cd card_game_judge\card_game_QA_manger
restart_translation.bat
```

选择模式3（完整翻译），确认后开始。

## 监控进度

翻译过程中会显示：
```
[1/4634] QA#5794 [问题] 调用Qwen API... 完成 [答案] 调用Qwen API... 完成 ✓
[2/4634] QA#5795 [问题] 调用Qwen API... 完成 [答案] 调用Qwen API... 完成 ✓
...
```

如果遇到配额用尽：
```
[100/4634] QA#5894 [问题] 调用Qwen API... 配额用尽
  ⚠️ 模型 qwen-turbo 免费配额已用尽
  ⚠️ 切换到模型: qwen-plus
  ↻ 使用新模型重试...
  调用Qwen API... 完成 [答案] 调用Qwen API... 完成 ✓
```

## 完成后检查

```bash
# 检查翻译质量
python check_translation_quality.py

# 查看结果
notepad official_qa_cn_qwen.json
```

目标：
- 日文残留: 0%
- 术语准确: 100%
- 语句流畅: 95%+

## 如果中断

不用担心！程序会：
1. 自动保存已翻译的内容到检查点
2. 下次运行时自动从断点继续
3. 不会重复翻译已完成的内容

重新运行：
```bash
python translate_qa_with_terminology.py
```

会自动检测检查点并继续。
