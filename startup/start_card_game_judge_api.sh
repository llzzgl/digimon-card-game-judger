#!/bin/bash
# 启动卡牌游戏裁判 FastAPI 后端
# 默认端口: 8000

cd "$(dirname "$0")/../card_game_judge"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python main.py --no_ui --port ${1:-8000}
