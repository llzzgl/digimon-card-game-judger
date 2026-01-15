#!/bin/bash
# 重建向量数据库
# 用于更新卡牌数据后重新构建知识库

cd "$(dirname "$0")/../card_game_judge"

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

python rebuild_vectordb.py
