# 翻译工具对比

## 两个版本的区别

### 1. OpenAI GPT-4 版本 (`translate_rulebook.py`)

**优点：**
- 翻译质量最高，理解能力强
- 对专业术语的处理更准确
- 上下文理解能力强

**缺点：**
- 成本较高（约 $0.03/1K tokens 输入，$0.06/1K tokens 输出）
- 需要 OpenAI API Key

**适合场景：**
- 需要最高质量的翻译
- 预算充足
- 对准确性要求极高

**配置：**
```bash
# .env 文件中添加
OPENAI_API_KEY=your_openai_api_key
```

**运行：**
```bash
python translate_rulebook.py
```

---

### 2. Google Gemini 版本 (`translate_rulebook_gemini.py`)

**优点：**
- 成本更低（Gemini Pro 免费额度较大）
- 速度较快
- 对日文支持良好

**缺点：**
- 翻译质量略低于 GPT-4
- 可能需要更多人工校对

**适合场景：**
- 预算有限
- 需要快速翻译
- 可以接受后期人工校对

**配置：**
```bash
# .env 文件中添加
GOOGLE_API_KEY=your_google_api_key
```

**运行：**
```bash
python translate_rulebook_gemini.py
```

---

## 成本估算

假设日文规则书约 20,000 字符：

### OpenAI GPT-4
- 输入 tokens: ~25,000 (包括术语表和原文)
- 输出 tokens: ~20,000 (翻译结果)
- 估算成本: ~$1.95

### Google Gemini Pro
- 免费额度: 60 requests/minute
- 超出后成本极低
- 估算成本: $0 - $0.50

---

## 推荐使用流程

1. **首次尝试**：使用 Gemini 版本快速翻译，查看效果
2. **质量评估**：检查翻译质量，特别是专业术语
3. **精细翻译**：如果需要更高质量，使用 GPT-4 版本
4. **混合使用**：可以用 Gemini 翻译大部分内容，GPT-4 翻译关键章节

---

## 获取 API Key

### OpenAI API Key
1. 访问 https://platform.openai.com/
2. 注册/登录账号
3. 进入 API Keys 页面创建新 key

### Google API Key
1. 访问 https://makersuite.google.com/app/apikey
2. 使用 Google 账号登录
3. 创建 API key

---

## 提示

- 两个版本都会自动从旧版中文规则书提取术语
- 建议先用小文件测试，确认效果
- 翻译结果都需要人工审核
- 可以根据预算和质量要求选择合适的版本
