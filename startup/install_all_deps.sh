#!/bin/bash
# 安装所有项目依赖

SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== 安装 card_game_judge 依赖 ==="
pip install -r "$PROJECT_ROOT/card_game_judge/requirements.txt"

echo ""
echo "=== 安装 card_data_scraper 依赖 ==="
pip install -r "$PROJECT_ROOT/card_data_scraper/requirements.txt"

echo ""
echo "=== 安装 digimon_data 依赖 ==="
pip install -r "$PROJECT_ROOT/digimon_data/requirements.txt"

echo ""
echo "=== 安装 digimon_card_data_chiness 依赖 ==="
pip install -r "$PROJECT_ROOT/digimon_card_data_chiness/requirements.txt"

echo ""
echo "=== 所有依赖安装完成 ==="
