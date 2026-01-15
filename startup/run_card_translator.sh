#!/bin/bash
# 运行卡牌翻译工具
# 需要配置 GOOGLE_API_KEY 或 OPENAI_API_KEY

cd "$(dirname "$0")/../digimon_data"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python translate_cards.py "$@"
