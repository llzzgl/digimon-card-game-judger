#!/bin/bash
# 运行日文卡牌数据爬虫 (digimoncard.com)
# 输出目录: ../digimon_card_data

cd "$(dirname "$0")/../card_data_scraper"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python scraper_v2.py
