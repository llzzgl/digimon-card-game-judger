#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
合并 LoRA 权重到基础模型
这样可以避免加载时的兼容性问题
"""
import os
import sys
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge_lora_weights(
    lora_path: str = "finetune/output/dtcg_qwen_lora",
    base_model: str = "Qwen/Qwen2-1.5B-Instruct",
    output_path: str = "finetune/output/dtcg_qwen_merged"
):
    """
    合并 LoRA 权重到基础模型
    
    Args:
        lora_path: LoRA 适配器路径
        base_model: 基础模型名称
        output_path: 输出路径
    """
    print("=" * 60)
    print("合并 LoRA 权重到基础模型")
    print("=" * 60)
    print(f"\n基础模型: {base_model}")
    print(f"LoRA 路径: {lora_path}")
    print(f"输出路径: {output_path}\n")
    
    # 1. 加载基础模型
    print("📥 步骤 1/4: 加载基础模型...")
    base_model_obj = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    print("✅ 基础模型加载完成")
    
    # 2. 加载 LoRA 适配器
    print("\n📥 步骤 2/4: 加载 LoRA 适配器...")
    model = PeftModel.from_pretrained(
        base_model_obj,
        lora_path,
        is_trainable=False
    )
    print("✅ LoRA 适配器加载完成")
    
    # 3. 合并权重
    print("\n🔄 步骤 3/4: 合并权重...")
    merged_model = model.merge_and_unload()
    print("✅ 权重合并完成")
    
    # 4. 保存合并后的模型
    print(f"\n💾 步骤 4/4: 保存到 {output_path}...")
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    merged_model.save_pretrained(output_path)
    
    # 保存分词器
    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        trust_remote_code=True
    )
    tokenizer.save_pretrained(output_path)
    
    print("✅ 模型保存完成")
    
    print("\n" + "=" * 60)
    print("✅ 合并完成！")
    print("=" * 60)
    print(f"\n合并后的模型保存在: {output_path}")
    print("\n使用方法:")
    print("  1. 修改 .env 文件:")
    print(f"     FINETUNED_BASE_MODEL={output_path}")
    print(f"     FINETUNED_LORA_PATH=  # 留空或删除这行")
    print("\n  2. 或者直接使用合并后的模型:")
    print("     from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"     model = AutoModelForCausalLM.from_pretrained('{output_path}')")
    print(f"     tokenizer = AutoTokenizer.from_pretrained('{output_path}')")
    
    return str(output_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="合并 LoRA 权重")
    parser.add_argument("--lora-path", type=str, 
                        default="finetune/output/dtcg_qwen_lora",
                        help="LoRA 适配器路径")
    parser.add_argument("--base-model", type=str,
                        default="Qwen/Qwen2-1.5B-Instruct",
                        help="基础模型名称")
    parser.add_argument("--output", type=str,
                        default="finetune/output/dtcg_qwen_merged",
                        help="输出路径")
    
    args = parser.parse_args()
    
    try:
        merge_lora_weights(
            lora_path=args.lora_path,
            base_model=args.base_model,
            output_path=args.output
        )
    except Exception as e:
        print(f"\n❌ 合并失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
