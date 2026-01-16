#!/bin/bash
# 启动向量数据库管理工具 GUI

cd "$(dirname "$0")/../card_game_judge"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python vectordb_manager_ui.py
