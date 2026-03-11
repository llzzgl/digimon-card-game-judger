#!/bin/bash

echo "============================================================"
echo "DTCG 裁判助手 - 使用微调模型"
echo "============================================================"
echo ""

# 设置使用微调模型
export LLM_MODEL=finetuned
export FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
export FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct

echo "配置信息:"
echo "  模型类型: 微调模型 (finetuned)"
echo "  LoRA 路径: $FINETUNED_LORA_PATH"
echo "  基础模型: $FINETUNED_BASE_MODEL"
echo ""

echo "正在启动服务..."
echo ""

python main.py
