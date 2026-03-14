# DTCG Database Updater Skill

数码宝贝卡牌数据库一键更新技能包

## 快速开始

### Windows

```bash
cd D:\LLMProject\dtcg_judger\db_updater_skill
.\scripts\update_all.bat
```

### Linux/Mac

```bash
cd /path/to/dtcg_judger/db_updater_skill
./scripts/update_all.sh
```

## 功能特性

- ✅ **一键更新** - 自动爬取、处理、构建数据库
- ✅ **数据格式一致** - 与项目现有数据格式完全相同
- ✅ **增量更新** - 跳过已存在数据，节省时间
- ✅ **自动备份** - 更新前自动备份现有数据
- ✅ **复用现有代码** - 基于原有爬虫重构，不重复造轮子

## 目录结构

```
db_updater_skill/
├── SKILL.md                  # 技能文档
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── config.py                 # 配置文件
├── main.py                   # 主入口
├── __init__.py              # 包初始化
├── scrapers/                # 爬虫模块
│   ├── jp_card_scraper.py   # 日文卡牌爬虫
│   └── qa_scraper.py        # QA 爬虫
├── database/                # 数据库管理
│   ├── card_db.py           # 卡牌数据库
│   └── qa_db.py             # QA 数据库
├── processors/              # 数据处理
└── scripts/                 # 脚本
    ├── update_all.bat       # Windows 一键更新
    └── update_all.sh        # Linux/Mac 一键更新
```

## 使用方法

### 方法 1: 一键脚本（推荐）

```bash
# Windows
.\scripts\update_all.bat

# Linux/Mac
./scripts/update_all.sh
```

### 方法 2: Python 调用

```python
from main import DatabaseUpdater

updater = DatabaseUpdater()
updater.update_all()  # 更新所有数据
```

### 方法 3: 单独更新

```python
from main import DatabaseUpdater

updater = DatabaseUpdater()

# 只更新日文卡牌
updater.update_jp_cards()

# 只更新 QA 数据
updater.update_qa()

# 重建数据库
updater.rebuild_database()
```

## 配置

编辑 `config.py` 自定义配置：

```python
CONFIG = {
    "jp_card": {
        "enabled": True,          # 是否启用
        "headless": True,         # 无头模式
        "delay": 0.5,             # 爬取延迟（秒）
        "output_path": "../digimon_card_data",
    },
    "qa": {
        "enabled": True,
        "languages": ["jp", "cn"],  # 语言
        "delay": 1.0,
    },
    "database": {
        "rebuild_on_update": False,  # 更新后是否重建
        "backup_before_update": True, # 更新前是否备份
    }
}
```

## 输出路径

- **日文卡牌**: `D:\LLMProject\dtcg_judger\digimon_card_data\`
- **中文卡牌**: `D:\LLMProject\dtcg_judger\digimon_card_data_chiness\`
- **QA 数据**: `D:\LLMProject\dtcg_judger\card_game_judge\card_game_QA_manger\`
- **合并数据库**: `D:\LLMProject\dtcg_judger\skill\data\`

## 依赖

- Python 3.8+
- Selenium 4.15+
- Chrome/Chromium 浏览器
- 其他依赖见 `requirements.txt`

### 安装依赖

```bash
pip install -r requirements.txt
```

## 数据格式

### 卡牌数据

```json
{
  "card_no": "BT24-001",
  "card_name": "BT24-001 ギギモン",
  "card_type": "デジタマ",
  "color": "赤",
  "level": 2,
  "effect": "【自分のターン】...",
  "rarity": "C",
  "pack_name": "ブースターパック TIME STRANGER【BT-24】"
}
```

### QA 数据

```json
{
  "id": "5794",
  "question": "セキュリティをチェックしたとき...",
  "answer": "【セキュリティ】効果が優先して発揮されます。",
  "language": "ja",
  "source": "digimoncard.com"
}
```

## 自动化流程

一键更新脚本执行以下步骤：

1. **检查环境** - 验证 Python 和依赖
2. **备份数据** - 备份现有数据到 `backups/` 目录
3. **爬取日文卡牌** - 从 digimoncard.com 爬取
4. **爬取 QA 数据** - 从 digimoncard.com 爬取
5. **数据处理** - 格式化、去重、标准化
6. **数据库构建** - 合并数据并输出
7. **验证** - 检查输出文件完整性

## 故障排除

### ChromeDriver 下载失败

```bash
# 手动下载 ChromeDriver
# https://chromedriver.chromium.org/downloads
# 放到 PATH 中或项目根目录
```

### 爬取速度慢

正常现象，为避免封禁设置了延迟。可在 `config.py` 中调整 `delay` 参数。

### 内存不足

全量爬取时数据量较大，建议至少 4GB 可用内存。

### 网络连接问题

确保能访问：
- https://digimoncard.com
- https://app.digicamoe.cn

## 备份管理

备份位置：`db_updater_skill/backups/`

每次更新前会自动创建带时间戳的备份目录。

## 更新日志

- **2026-03-12**: 初始版本
  - 整合所有爬虫代码
  - 一键更新脚本
  - 数据库管理模块
  - 自动备份功能

## 许可证

与主项目保持一致

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

DTCG Judger Team
