#!/bin/bash
# DTCG 微调训练脚本

echo "=========================================="
echo "DTCG 规则微调训练"
echo "=========================================="
echo ""
echo "如果 bitsandbytes 有问题，使用不带量化的版本"
echo ""

# 推荐：不使用量化（最稳定，需要 8-12GB 显存）
python finetune_qwen_no_quant.py \
    --model "Qwen/Qwen2-1.5B-Instruct" \
    --data "training_data/dtcg_finetune_data.jsonl" \
    --output "output/dtcg_qwen_lora" \
    --epochs 3 \
    --batch_size 1 \
    --max_length 512 \
    --lora_r 64

# 如果显存不足，降低参数
# python finetune_qwen_no_quant.py --batch_size 1 --max_length 256 --lora_r 32

# 如果 bitsandbytes 工作正常，可以尝试量化版本
# python finetune_qwen.py --use_8bit
