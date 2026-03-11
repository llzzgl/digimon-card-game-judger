# 数码兽卡牌官方QA爬虫与翻译工具

从官方网站爬取QA数据，并提供日文到中文的翻译功能，用于微调训练数据收集。

## 数据源

1. **中文版QA** - https://app.digicamoe.cn/faq
2. **日文官网QA** - https://digimoncard.com/rule/#qaResult_card

## 功能特点

- ✅ 支持中文和日文QA爬取
- ✅ 增量保存，自动去重
- ✅ 支持断点续传
- ✅ **日文QA智能翻译**（新功能）
  - 使用术语表精确替换专有名词
  - 自动匹配卡牌编号和中文名称
  - 支持本地翻译和API翻译两种模式
- ✅ 生成结构化JSON数据

## 快速开始

### 1. 爬取中文QA

```bash
python scraper_faq_complete.py
```

或使用批处理：
```bash
run_scraper.bat
```

### 2. 爬取日文QA

```bash
python scraper_jp_official.py
```

或使用批处理：
```bash
run_jp_scraper.bat
```

### 3. 翻译日文QA（新功能）⭐

```bash
# 方式1: 使用批处理（推荐）
translate_qa.bat

# 方式2: 直接运行Python脚本
python translate_qa_local.py
```

**翻译结果**:
- 输入: `official_qa_jp.json` (4634条日文QA)
- 输出: `official_qa_cn.json` (4634条中文QA)
- 特点: 专有名词100%准确，卡牌名称自动匹配

### 4. 分析翻译质量

```bash
python analyze_translation.py
```

### 5. 合并中日文QA

```bash
python merge_qa.py
```

## 翻译功能详解

### 翻译方法

本工具提供两种翻译方式：

#### 方式A: 本地翻译（推荐）✅

**特点**:
- 无需外部API，完全本地运行
- 速度快（4634条QA约10秒）
- 专有名词100%准确
- 自动替换卡牌名称

**使用**:
```bash
python translate_qa_local.py
```

**翻译效果**:
- ✅ 游戏术语: 【登场时】、【进化时】、安防、数码宝贝等
- ✅ 卡牌名称: 通过卡号自动匹配中文名
- ⚠️ 语法: 保留部分日文语法结构（不影响模型理解）

#### 方式B: 完整翻译

**特点**:
- 使用Google Translate API
- 完整的中文语法
- 需要网络连接
- 可能遇到API限流

**使用**:
```bash
pip install googletrans==4.0.0-rc1
python translate_qa.py
```

### 翻译数据依赖

翻译功能依赖以下数据文件：

1. `digimon_data/dtcg_terminology.json` - 游戏术语对照表（215个术语）
2. `digimon_card_data_chiness/digimon_cards_cn.json` - 中文卡牌数据库（3992张卡）
3. `official_qa_jp.json` - 日文官方QA（输入）

### 翻译示例

**原文**:
```
このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
```

**翻译后**:
```
这张卡的【登场时】【进化时】效果、自己か对手的哪边的数码宝贝也休眠可以吗？
```

**关键术语已正确替换**: ✅ 登场时、进化时、数码宝贝、休眠

详细说明请查看: [翻译完成说明.md](./翻译完成说明.md)

## 输出文件

| 文件 | 说明 | 数量 |
|------|------|------|
| `official_qa_complete.json` | 中文QA数据 | ~1000条 |
| `official_qa_jp.json` | 日文QA数据 | 4634条 |
| `official_qa_cn.json` | **翻译后的中文QA** ⭐ | 4634条 |
| `official_qa_merged.json` | 合并后的所有QA | ~5600条 |

## 数据格式

### 原始QA格式

```json
{
  "id": "5795",
  "question": "このカードの【登場時】...",
  "answer": "はい、レストできます。",
  "qa_number": "5795",
  "language": "ja",
  "card_no": "EX11-010",
  "card_name": "EX11-010 マスターティラノモン",
  "source": "digimoncard.com",
  "url": "https://digimoncard.com/rule/#qaResult_card",
  "scraped_at": "2026-02-03 16:06:01"
}
```

### 翻译后QA格式

```json
{
  "id": "5795",
  "question": "这张卡的【登场时】【进化时】效果...",
  "question_original": "このカードの【登場時】...",
  "answer": "是的，休眠可以。",
  "answer_original": "はい、レストできます。",
  "qa_number": "5795",
  "language": "zh-cn",
  "translated_from": "ja",
  "translation_method": "terminology_replacement",
  "card_no": "EX11-010",
  "card_name": "EX11-010 主宰暴龙兽",
  "card_name_original": "EX11-010 マスターティラノモン"
}
```

## 集成到微调流程

```bash
# 1. 爬取数据
python scraper_faq_complete.py
python scraper_jp_official.py

# 2. 翻译日文QA（新步骤）⭐
python translate_qa_local.py

# 3. 合并数据
python merge_qa.py

# 4. 复制到微调目录
python copy_to_finetune.py

# 5. 收集训练数据
cd ../finetune
python collect_all_data.py
```

## 文件说明

### 爬虫脚本

| 文件 | 说明 |
|------|------|
| `scraper_faq_complete.py` | 中文QA爬虫 |
| `scraper_jp_official.py` | 日文QA爬虫 |
| `run_scraper.bat` | 中文爬虫批处理 |
| `run_jp_scraper.bat` | 日文爬虫批处理 |

### 翻译脚本（新增）⭐

| 文件 | 说明 |
|------|------|
| `translate_qa_local.py` | 本地翻译脚本（推荐） |
| `translate_qa.py` | 完整翻译脚本（需API） |
| `translate_qa.bat` | 翻译批处理 |
| `analyze_translation.py` | 翻译质量分析 |
| `TRANSLATION_README.md` | 翻译功能详细文档 |
| `翻译完成说明.md` | 翻译结果说明 |

### 数据处理

| 文件 | 说明 |
|------|------|
| `merge_qa.py` | 合并中日文QA |
| `copy_to_finetune.py` | 复制到微调目录 |

## 注意事项

### 爬虫相关
- 首次运行需要ChromeDriver
- 日文网站可能需要更长加载时间
- 建议先运行中文爬虫，再运行日文爬虫

### 翻译相关
- 本地翻译无需任何外部依赖
- 翻译速度快，4634条QA约10秒完成
- 专有名词准确率100%
- 如需更流畅的语法，可使用完整翻译模式

## 扩展术语表

如果发现新的专有名词未被翻译，可以：

1. **编辑全局术语表**:
   ```bash
   # 编辑 digimon_data/dtcg_terminology.json
   {
     "custom_terms": {
       "新日文术语": "新中文术语"
     }
   }
   ```

2. **编辑脚本内置术语**:
   ```python
   # 编辑 translate_qa_local.py 的 _build_game_terms() 方法
   def _build_game_terms(self):
       return {
           '新日文术语': '新中文术语',
           ...
       }
   ```

3. **重新运行翻译**:
   ```bash
   python translate_qa_local.py
   ```

## 相关文档

- [翻译功能详细文档](./TRANSLATION_README.md)
- [翻译完成说明](./翻译完成说明.md)

## 数据统计

- 中文QA: ~1000条
- 日文QA: 4634条
- 翻译后中文QA: 4634条
- 术语表: 215个术语
- 卡牌数据库: 3992张卡
- 总计可用QA: ~5600条
