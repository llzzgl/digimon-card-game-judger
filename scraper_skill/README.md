# DTCG Scraper Skill - 数码宝贝卡牌爬虫技能

## 概述

这是一个独立于主裁定功能的爬虫技能包，提供数码宝贝卡牌数据的爬取能力。

**设计原则**：
- ✅ 不改动原有爬虫文件 - 保持原样
- ✅ 新建测试文件夹 - `scraper_skill/data/output/`
- ✅ 输出路径一致 - 最终输出到原路径

## 目录结构

```
scraper_skill/
├── src/
│   ├── __init__.py           # 包初始化
│   ├── card_scraper.py       # 卡牌爬虫统一接口
│   ├── qa_scraper.py         # QA 爬虫统一接口
│   └── utils/
│       ├── __init__.py
│       ├── jp_scraper.py     # 日文爬虫
│       ├── cn_scraper.py     # 中文爬虫
│       └── digimon_scraper.py # 数码兽图鉴爬虫
├── data/
│   └── output/               # 爬取数据输出（测试用）
├── config/
│   └── scraper_config.py     # 爬虫配置
├── tests/
│   └── test_scrapers.py      # 测试脚本
└── README.md                 # 本文档
```

## 功能模块

### 1. 日文卡牌爬虫 (`JapaneseCardScraper`)

基于原有 `card_data_scraper_JP/scraper.py` 重构

**功能**：
- 爬取 digimoncard.com 的日文卡牌信息
- 支持单个卡包或全部卡包爬取
- 输出 JSON 格式卡牌数据

**使用示例**：
```python
from src.utils.jp_scraper import JapaneseCardScraper

scraper = JapaneseCardScraper({"headless": True})
pack, cards = scraper.scrape_pack("503035")  # 爬取指定卡包
scraper.save_to_json(cards, Path("output/cards_jp.json"))
scraper.close()
```

### 2. 中文卡牌爬虫 (`ChineseCardScraper`)

基于原有 `digimon_card_data_chiness/scraper_v3.py` 重构

**功能**：
- 爬取 app.digicamoe.cn 的中文卡牌信息
- 支持增量爬取（跳过已存在的卡牌）
- 自动保存进度

**使用示例**：
```python
from src.utils.cn_scraper import ChineseCardScraper

scraper = ChineseCardScraper({
    "headless": True,
    "output_path": "digimon_cards_cn.json"
})
new_count = scraper.scrape_all_cards(max_pages=5)  # 爬取 5 页
scraper.close()
```

### 3. 数码兽图鉴爬虫 (`DigimonNameScraper`)

基于原有 `digimon_data/digimon_name_scraper_v3.py` 重构

**功能**：
- 从 digimons.net 爬取数码兽中日文名称对照
- 支持批量爬取和单条查询

**使用示例**：
```python
from src.utils.digimon_scraper import DigimonNameScraper

scraper = DigimonNameScraper({"delay": 0.2})
mapping = scraper.scrape_all()  # 爬取所有
scraper.save_mapping(Path("digimon_name_mapping.json"))

# 查询
chinese_name = scraper.get_chinese_name("アグモン")
```

### 4. QA 爬虫 (`QAScraper`)

基于原有 `src/scraper/qa/card_game_QA_manger/scraper_jp_official.py` 重构

**功能**：
- 爬取 digimoncard.com 的官方 QA 裁定
- 支持按卡包分类爬取
- 支持搜索和按卡牌编号查询

**使用示例**：
```python
from src.qa_scraper import QAScraper

scraper = QAScraper({
    "headless": True,
    "output_path": "rulings.json"
})
new_count = scraper.scrape_japanese_official()  # 爬取日文官网 QA

# 搜索
results = scraper.search_qa("安防")
card_rulings = scraper.get_qa_by_card("BT24-001")
```

### 5. 统一接口 (`CardScraper`)

整合日文和中文卡牌爬虫的统一接口

**功能**：
- 统一管理日文和中文爬虫
- 支持数据合并
- 提供数据验证功能

**使用示例**：
```python
from src.card_scraper import CardScraper

scraper = CardScraper({
    "output_path": "skill/data/cards.json"
})

# 爬取日文卡牌
jp_cards = scraper.scrape_japanese(
    category_ids=["503035"],
    output_path=Path("output/cards_jp.json")
)

# 爬取中文卡牌
cn_new = scraper.scrape_chinese(max_pages=10)

# 合并数据
scraper.merge_cards(
    jp_path=Path("output/cards_jp.json"),
    cn_path=Path("digimon_cards_cn.json")
)

# 保存合并结果
scraper.save_merged()

# 验证数据
report = scraper.validate_cards()
```

## 配置说明

配置文件：`config/scraper_config.py`

### 输出路径配置

```python
OUTPUT_PATHS = {
    "cards": "skill/data/cards.json",           # 卡牌数据
    "rulings": "skill/data/rulings.json",       # QA 裁定数据
    "digimon_mapping": "digimon_data/digimon_name_mapping_v3.json",
    "cards_cn": "digimon_card_data_chiness/digimon_cards_cn.json",
    "cards_jp": "card_data_scraper_JP/output/cards.json",
}
```

### 爬虫设置

```python
SCRAPER_CONFIG = {
    "default_timeout": 30,          # 默认超时时间（秒）
    "retry_times": 3,               # 重试次数
    "retry_delay": 2,               # 重试延迟（秒）
    "request_delay": 1,             # 请求间隔（秒）
    "headless": True,               # 无头模式
    "window_width": 1920,
    "window_height": 1080,
}
```

## 测试

运行测试脚本：

```bash
cd D:\LLMProject\dtcg_judger
python scraper_skill/tests/test_scrapers.py
```

测试内容包括：
- ✅ 配置加载
- ✅ 各模块导入
- ✅ 实例化
- ✅ 现有数据加载
- ✅ 数据验证

## 依赖

```txt
selenium>=4.15.0
webdriver-manager>=4.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
```

安装依赖：

```bash
pip install -r card_data_scraper_JP/requirements.txt
pip install -r digimon_card_data_chiness/requirements.txt
pip install -r digimon_data/requirements.txt
```

## 输出数据格式

### 卡牌数据 (cards.json)

```json
[
  {
    "card_no": "BT24-001",
    "card_name": "プロットモン",
    "card_name_ruby": "プロットモン",
    "card_type": "デジモン",
    "color": "白",
    "level": 3,
    "cost": 3,
    "dp": 4000,
    "effect": "このデジモンは攻撃できない。",
    "rarity": "C"
  }
]
```

### QA 裁定数据 (rulings.json)

```json
[
  {
    "id": "Q1234",
    "qa_number": "Q1234",
    "question": "「セキュリティアタック」は何ですか？",
    "answer": "セキュリティアタックとは、相手のセキュリティをチェックする攻撃です。",
    "card_no": "BT24-001",
    "card_name": "プロットモン",
    "language": "ja",
    "scraped_at": "2026-03-12T10:00:00"
  }
]
```

### 数码兽名称映射 (digimon_name_mapping.json)

```json
{
  "アグモン": "亚古兽",
  "ガブモン": "加布兽",
  "ピヨモン": "比丘兽"
}
```

## 错误处理

所有爬虫模块都包含：
- ✅ 重试机制（默认 3 次）
- ✅ 超时处理（默认 30 秒）
- ✅ 详细日志输出
- ✅ 异常捕获和报告

## 注意事项

1. **网络请求**：爬虫需要访问外部网站，请确保网络连接正常
2. **ChromeDriver**：需要安装 Chrome 浏览器和对应版本的 ChromeDriver
3. **请求频率**：请遵守目标网站的 robots.txt 和访问频率限制
4. **数据备份**：爬取前建议备份现有数据文件

## 更新记录

- 2026-03-12: 初始版本，重构原有爬虫功能为独立 Skill

## 许可证

与原项目保持一致
