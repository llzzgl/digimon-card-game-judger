# DTCG 卡牌数据翻译工具

将日文 DTCG（数码宝贝卡牌游戏）卡牌数据翻译成中文。

## 翻译策略

1. **数码宝贝名称**: 使用数码宝贝图鉴官网 (http://digimons.net) 的官方中文名称
2. **游戏术语**: 使用 DTCG 规则书中的专有名词对照表
3. **效果文本**: 先用术语表替换，再用 AI 翻译剩余日文

## 文件说明

| 文件 | 说明 |
|------|------|
| `digimon_name_scraper_v3.py` | 数码宝贝图鉴爬虫，从官网爬取中日文名称对照 |
| `digimon_name_mapping_v3.json` | 数码宝贝日文-中文名称映射数据 |
| `dtcg_terminology.py` | DTCG 专有名词术语表（Python模块） |
| `dtcg_terminology.json` | 术语表 JSON 格式 |
| `card_translator.py` | 卡牌翻译器核心代码 |
| `translate_cards.py` | 翻译主程序入口 |
| `requirements.txt` | Python 依赖 |

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# Gemini API (推荐)
GOOGLE_API_KEY=your_google_api_key

# 或 OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

### 3. 运行翻译

```bash
cd digimon_data
python translate_cards.py
```

翻译后的文件将保存在 `translated_cards/` 目录。

### 4. 更新名称映射（可选）

如需重新爬取数码宝贝名称：

```bash
python digimon_name_scraper_v3.py
```

## 术语对照表

| 类别 | 日文 | 中文 |
|------|------|------|
| 卡牌类型 | デジタマ / デジモン / テイマー / オプション | 数码蛋 / 数码宝贝 / 驯兽师 / 选项 |
| 颜色 | 赤 / 青 / 黄 / 緑 / 黒 / 紫 / 白 | 红 / 蓝 / 黄 / 绿 / 黑 / 紫 / 白 |
| 形态 | 幼年期 / 成長期 / 成熟期 / 完全体 / 究極体 | 幼年期 / 成长期 / 成熟期 / 完全体 / 究极体 |
| 属性 | ワクチン種 / データ種 / ウィルス種 / フリー種 | 疫苗种 / 数据种 / 病毒种 / 自由种 |

## 注意事项

- AI 翻译需要网络连接和有效的 API Key
- 大量翻译可能产生 API 费用
- 翻译结果保留日文原文便于校对
