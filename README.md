# Digimon Card Game Judger

基于 RAG 的数码宝贝卡牌游戏智能裁判系统。



## 项目结构

```
├── card_game_judge/        # 智能裁判主程序 (RAG + Web UI)
├── card_data_scraper/      # 日文卡牌数据爬虫
├── digimon_card_data/      # 日文卡牌数据 (JSON)
├── digimon_card_data_chiness/  # 中文卡牌数据爬虫 + 数据
├── digimon_data/           # 数码宝贝名称映射 & 翻译工具
├── data/chroma_db/         # 向量数据库
└── startup/                # 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
# 方式一：使用启动脚本（Git Bash / WSL）
cd startup
./install_all_deps.sh

# 方式二：手动安装
pip install -r card_game_judge/requirements.txt
pip install -r card_data_scraper/requirements.txt
pip install -r digimon_data/requirements.txt
pip install -r digimon_card_data_chiness/requirements.txt
```

### 2. 配置环境变量

```bash
cd card_game_judge
cp .env.example .env
# 编辑 .env 文件，填入 API Key
```

## 功能启动顺序

完整流程按以下顺序执行：

### Step 1: 爬取卡牌数据

```bash
# 爬取日文卡牌数据
cd card_data_scraper
python scraper_v2.py

# 爬取中文卡牌数据
cd digimon_card_data_chiness
python scraper_v3.py

# 爬取数码宝贝名称映射（日中对照）
cd digimon_data
python digimon_name_scraper_v3.py
```

### Step 2: 翻译卡牌数据（可选）

```bash
cd digimon_data
python translate_cards.py
```

### Step 3: 构建向量数据库

```bash
cd card_game_judge
python rebuild_vectordb.py
```

### Step 4: 启动智能裁判

```bash
cd card_game_judge

# 启动 Web UI（推荐）
python main.py --port 8000

# 或启动 API 服务
python main.py --no_ui --port 8000
```

访问 http://localhost:8000 使用 Web 界面。

## 启动脚本（Git Bash / WSL）

| 脚本 | 功能 |
|------|------|
| `startup/start_card_game_judge_ui.sh` | 启动 Web UI |
| `startup/start_card_game_judge_api.sh` | 启动 API 服务 |
| `startup/run_card_scraper_jp.sh` | 爬取日文卡牌 |
| `startup/run_card_scraper_cn.sh` | 爬取中文卡牌 |
| `startup/run_digimon_name_scraper.sh` | 爬取名称映射 |
| `startup/run_card_translator.sh` | 翻译卡牌 |
| `startup/rebuild_vectordb.sh` | 重建向量库 |

## 批量导入文档

```bash
cd card_game_judge
python main.py --batch-import ../digimon_card_data --doc-type rule --pattern "*.json"
```

## 常见问题

网络问题请参考 `card_game_judge/网络问题解决方案.md`
