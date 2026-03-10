#!/bin/bash

echo "============================================================"
echo "安装微调模型依赖"
echo "============================================================"
echo ""

echo "正在安装必需的库..."
echo ""

pip install peft transformers accelerate bitsandbytes torch

echo ""
echo "============================================================"
echo "安装完成！"
echo "============================================================"
echo ""
echo "现在可以运行:"
echo "  python main.py"
echo "或"
echo "  ./start_with_finetuned.sh"
echo ""
