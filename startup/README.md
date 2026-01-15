# 启动脚本说明

本文件夹包含项目各功能的启动脚本。

## 使用前准备

```bash
# 首次使用，安装所有依赖
./install_all_deps.sh
```

## 脚本列表

| 脚本 | 功能 |
|------|------|
| `start_card_game_judge_ui.sh` | 启动卡牌裁判 Web UI (Streamlit) |
| `start_card_game_judge_api.sh` | 启动卡牌裁判 API 服务 (FastAPI) |
| `run_card_scraper_jp.sh` | 爬取日文卡牌数据 |
| `run_card_scraper_cn.sh` | 爬取中文卡牌数据 |
| `run_digimon_name_scraper.sh` | 爬取数码宝贝日中名称映射 |
| `run_card_translator.sh` | 翻译卡牌数据 |
| `rebuild_vectordb.sh` | 重建向量数据库 |
| `install_all_deps.sh` | 安装所有项目依赖 |

## Windows 用户

在 Git Bash 或 WSL 中运行这些脚本，或参考脚本内容手动执行 Python 命令。
