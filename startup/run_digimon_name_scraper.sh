#!/bin/bash
# 运行数码宝贝名称爬虫 (日中名称映射)
# 输出: ../digimon_data/digimon_name_mapping_v3.json

cd "$(dirname "$0")/../digimon_data"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python digimon_name_scraper_v3.py
