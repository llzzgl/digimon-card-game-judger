#!/bin/bash
# 运行中文卡牌数据爬虫
# 输出: ../digimon_card_data_chiness/digimon_cards_cn.json

cd "$(dirname "$0")/../digimon_card_data_chiness"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python scraper_v3.py
