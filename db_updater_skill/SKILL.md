# DTCG Database Updater Skill - 数码宝贝卡牌数据库更新技能

## 概述

这是一个用于一键更新/创建数码宝贝卡牌数据库的技能包。提供卡牌数据、QA 裁定数据的爬取、格式转换和数据库构建功能。

**核心原则**：
- ✅ 数据格式与现有项目完全一致
- ✅ 支持增量更新和全量重建
- ✅ 一键调用，自动化流程
- ✅ 支持日文和中文数据源

## 目录结构

```
db_updater_skill/
├── SKILL.md                  # 本文档
├── requirements.txt          # 依赖包
├── __init__.py              # 包初始化
├── main.py                  # 主入口脚本
├── config.py                # 配置管理
├── scrapers/
│   ├── __init__.py
│   ├── jp_card_scraper.py   # 日文卡牌爬虫
│   ├── cn_card_scraper.py   # 中文卡牌爬虫
│   └── qa_scraper.py        # QA 爬虫
├── processors/
│   ├── __init__.py
│   ├── card_processor.py    # 卡牌数据处理
│   └── qa_processor.py      # QA 数据处理
├── database/
│   ├── __init__.py
│   ├── card_db.py           # 卡牌数据库管理
│   └── qa_db.py             # QA 数据库管理
└── scripts/
    ├── update_all.bat       # Windows 一键更新脚本
    └── update_all.sh        # Linux/Mac 一键更新脚本
```

## 快速开始

### 一键更新（推荐）

```bash
# Windows
cd D:\LLMProject\dtcg_judger\db_updater_skill
.\scripts\update_all.bat

# Linux/Mac
cd /path/to/dtcg_judger/db_updater_skill
./scripts/update_all.sh
```

### 手动调用

```python
from main import DatabaseUpdater

updater = DatabaseUpdater()

# 更新所有数据
updater.update_all()

# 只更新日文卡牌
updater.update_jp_cards()

# 只更新 QA 数据
updater.update_qa()

# 重建数据库
updater.rebuild_database()
```

## 配置选项

在 `config.py` 中配置：

```python
CONFIG = {
    "jp_card": {
        "enabled": True,
        "output_path": "../digimon_card_data",
        "incremental": True,
    },
    "cn_card": {
        "enabled": True,
        "output_path": "../digimon_card_data_chiness",
        "incremental": True,
    },
    "qa": {
        "enabled": True,
        "output_path": "../card_game_judge/card_game_QA_manger",
        "languages": ["jp", "cn"],
    },
    "database": {
        "output_path": "../skill/data",
        "rebuild_on_update": False,
    }
}
```

## 数据格式

### 卡牌数据格式

```json
{
  "card_no": "BT24-001",
  "card_name": "BT24-001 ギギモン",
  "card_name_ruby": null,
  "card_type": "デジタマ",
  "color": "赤",
  "color2": null,
  "level": 2,
  "cost": null,
  "dp": null,
  "digivolve_cost1": null,
  "digivolve_cost2": null,
  "digivolve_color1": null,
  "digivolve_color2": null,
  "form": "幼年期",
  "attribute": null,
  "digimon_type": "レッサー型/リベレイター",
  "effect": "【自分のターン】[ターンに 1 回] 相手のセキュリティが減ったとき、DP3000 以下の相手のデジモン 1 体を消滅できる。",
  "inherited_effect": "【自分のターン】[ターンに 1 回] 相手のセキュリティが減ったとき、DP3000 以下の相手のデジモン 1 体を消滅できる。",
  "security_effect": null,
  "rarity": "C",
  "image_url": "https://digimoncard.com/images/cardlist/card/BT24-001.png?02",
  "parallel_id": null,
  "pack_id": "503035",
  "pack_name": "ブースターパック TIME STRANGER【BT-24】",
  "card_url": "javascript:void(0);",
  "created_at": "2026-01-14T10:41:42.961541"
}
```

### QA 数据格式

```json
{
  "id": "5794",
  "question": "セキュリティをチェックしたとき、【セキュリティ】効果と、「セキュリティをチェックしたとき」効果、「セキュリティが減ったとき」効果が同時誘発した場合、どの順で発揮しますか？\n2026/01/30 更新",
  "answer": "【セキュリティ】効果が優先して発揮されます。\n【セキュリティ】効果はチェックされた場合、発揮待ちにならずに即座に発揮されます。\nそれ以外の誘発した効果は、ターンプレイヤー側の効果から発揮させます。",
  "qa_number": "5794",
  "language": "ja",
  "source": "digimoncard.com",
  "url": "https://digimoncard.com/rule/#qaResult_card",
  "scraped_at": "2026-02-03 16:06:01",
  "prodid": "503036",
  "prod_name": "エクストラブースター DAWN OF LIBERATOR【EX-11】"
}
```

## 输出路径

默认输出到项目标准路径：

- **日文卡牌**: `D:\LLMProject\dtcg_judger\digimon_card_data\`
- **中文卡牌**: `D:\LLMProject\dtcg_judger\digimon_card_data_chiness\`
- **QA 数据**: `D:\LLMProject\dtcg_judger\card_game_judge\card_game_QA_manger\`
- **合并数据库**: `D:\LLMProject\dtcg_judger\skill\data\`

## 依赖安装

```bash
pip install -r requirements.txt
```

### 必需依赖

- selenium >= 4.15.0
- webdriver-manager >= 4.0.0
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- pandas >= 2.0.0
- tqdm >= 4.66.0

## 使用示例

### 示例 1: 更新日文卡牌

```python
from scrapers.jp_card_scraper import JapaneseCardScraper

scraper = JapaneseCardScraper(headless=True)
scraper.scrape_all_packs()
scraper.close()
```

### 示例 2: 更新 QA 数据

```python
from scrapers.qa_scraper import QAScraper

scraper = QAScraper(language="jp")
scraper.scrape_all()
scraper.close()
```

### 示例 3: 合并数据库

```python
from database.card_db import CardDatabase

db = CardDatabase()
db.load_from_folder("../digimon_card_data")
db.merge_and_deduplicate()
db.save_to_json("../skill/data/cards.json")
```

## 自动化流程

一键更新脚本执行以下步骤：

1. **安装依赖** - 检查并安装所需 Python 包
2. **爬取日文卡牌** - 从 digimoncard.com 爬取最新卡牌数据
3. **爬取中文卡牌** - 从 app.digicamoe.cn 爬取中文卡牌数据
4. **爬取 QA 数据** - 从 digimoncard.com 爬取官方 QA
5. **数据处理** - 格式化、去重、标准化
6. **数据库构建** - 合并数据并输出到标准路径
7. **验证** - 检查输出文件完整性

## 注意事项

1. **网络要求**: 需要能访问 digimoncard.com 和 app.digicamoe.cn
2. **浏览器驱动**: 首次运行会自动下载 ChromeDriver
3. **反爬虫**: 爬取时会自动添加延迟，避免被封禁
4. **数据备份**: 更新前会自动备份现有数据
5. **增量更新**: 默认跳过已存在的卡牌，节省时间

## 故障排除

### 常见问题

**Q: ChromeDriver 下载失败**
A: 检查网络连接，或手动下载 ChromeDriver 并放到 PATH 中

**Q: 爬取速度慢**
A: 正常现象，为避免封禁设置了延迟。可在 config.py 中调整 delay 参数

**Q: 数据格式不一致**
A: 检查源网站是否有结构变化，需更新爬虫选择器

**Q: 内存不足**
A: 全量爬取时数据量较大，建议至少 4GB 可用内存

## 更新日志

- 2026-03-12: 初始版本，整合所有爬虫和数据库构建功能
