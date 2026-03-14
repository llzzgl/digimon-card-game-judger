#!/bin/bash

echo "============================================================"
echo "DTCG Database Updater - 一键更新脚本"
echo "============================================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")/.."

echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 未安装或不在 PATH 中"
    echo "请先安装 Python 3.8+"
    exit 1
fi
echo "✓ Python 环境正常 ($(python3 --version))"

echo ""
echo "[2/4] 安装依赖..."
pip3 install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "✗ 依赖安装失败"
    exit 1
fi
echo "✓ 依赖安装完成"

echo ""
echo "[3/4] 开始更新数据..."
echo ""
python3 main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ 数据更新失败"
    exit 1
fi

echo ""
echo "[4/4] 验证输出..."
if [ -f "../skill/data/cards.json" ]; then
    echo "✓ 卡牌数据库已更新"
else
    echo "⚠ 卡牌数据库未生成"
fi

if [ -f "../skill/data/rulings.json" ]; then
    echo "✓ QA 数据库已更新"
else
    echo "⚠ QA 数据库未生成"
fi

echo ""
echo "============================================================"
echo "更新完成！"
echo "============================================================"
echo ""
