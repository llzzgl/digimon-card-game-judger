# DTCG规则书翻译工具

这个工具可以将日文版本的DTCG规则书翻译成中文，并自动保持与旧版中文规则书的术语一致性。

## 功能特点

1. **术语一致性**：自动从旧版中文规则书中提取专有名词，确保翻译使用相同的术语
2. **智能翻译**：使用GPT-4进行高质量翻译
3. **分块处理**：自动将长文本分块处理，避免token限制
4. **格式保留**：尽可能保留原文的格式和结构

## 使用方法

### 1. 确保环境配置

确保 `.env` 文件中配置了 OpenAI API Key：

```
OPENAI_API_KEY=your_api_key_here
```

### 2. 运行翻译

```bash
cd card_game_judge
python translate_rulebook.py
```

### 3. 查看结果

翻译完成后，结果会保存在：
```
数码宝贝卡牌对战_综合规则_最新版_中文翻译.txt
```

## 工作流程

1. **提取文本**：从两份PDF中提取文本内容
2. **构建术语表**：分析旧版中文规则书，提取关键术语
3. **分块翻译**：将日文规则书分块，逐块翻译
4. **保存结果**：合并所有翻译块，保存为文本文件

## 自定义配置

如果需要修改文件路径或翻译参数，可以编辑 `translate_rulebook.py` 中的 `main()` 函数：

```python
def main():
    # 修改这些路径
    chinese_ref = "数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf"
    japanese_new = "general_rule.pdf"
    output_file = "数码宝贝卡牌对战_综合规则_最新版_中文翻译.txt"
    
    translator = RulebookTranslator(chinese_ref, japanese_new)
    translator.translate_rulebook(output_file)
```

## 注意事项

- 翻译过程需要调用OpenAI API，会产生费用
- 翻译时间取决于规则书长度，可能需要几分钟
- 建议先用小文件测试，确认效果后再处理完整文档
- 翻译结果建议人工审核，特别是专业术语部分

## 高级用法

### 调整翻译模型

在代码中可以修改使用的模型：

```python
model="gpt-4"  # 可改为 "gpt-4-turbo" 或 "gpt-3.5-turbo"
```

### 调整分块大小

```python
chunks = self.split_text_into_chunks(japanese_text, max_chars=2000)  # 修改这个数字
```

### 调整温度参数

```python
temperature=0.3  # 降低获得更确定的翻译，提高获得更多样的表达
```
