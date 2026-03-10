#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bitsandbytes 问题诊断和修复脚本
"""
import sys
import subprocess
import torch

print("=" * 60)
print("bitsandbytes 问题诊断")
print("=" * 60)

# 检查 CUDA 版本
print(f"\n✅ PyTorch 版本: {torch.__version__}")
print(f"✅ CUDA 版本: {torch.version.cuda}")
print(f"✅ CUDA 可用: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"✅ 计算能力: {props.major}.{props.minor}")

# 检查 bitsandbytes
try:
    import bitsandbytes as bnb
    print(f"\n✅ bitsandbytes 版本: {bnb.__version__}")
    
    # 测试 8-bit 矩阵乘法
    print("\n🧪 测试 8-bit 矩阵乘法...")
    try:
        # 简单的 8-bit 测试
        x = torch.randn(10, 10).cuda().half()
        y = torch.randn(10, 10).cuda().half()
        z = torch.matmul(x, y)
        print("✅ 基础矩阵乘法测试通过")
        
        # 测试 Linear8bitLt
        from bitsandbytes.nn import Linear8bitLt
        layer = Linear8bitLt(10, 10, has_fp16_weights=False).cuda()
        out = layer(x)
        print("✅ 8-bit Linear 层测试通过")
        
    except Exception as e:
        print(f"❌ 8-bit 测试失败: {e}")
        print("\n这表明 bitsandbytes 与你的 CUDA 环境不兼容")
        
except ImportError as e:
    print(f"\n❌ bitsandbytes 未安装: {e}")

print("\n" + "=" * 60)
print("推荐解决方案")
print("=" * 60)

cuda_version = torch.version.cuda
if cuda_version:
    major_version = cuda_version.split('.')[0]
    print(f"\n你的 CUDA 版本: {cuda_version}")
    
    print("\n方案 1: 重新安装 bitsandbytes（推荐）")
    print("---------------------------------------")
    print("pip uninstall bitsandbytes -y")
    
    if major_version == "11":
        print("pip install bitsandbytes")
    elif major_version == "12":
        print("pip install bitsandbytes")
    else:
        print("pip install bitsandbytes")
    
    print("\n方案 2: 从源码编译 bitsandbytes")
    print("---------------------------------------")
    print("git clone https://github.com/TimDettmers/bitsandbytes.git")
    print("cd bitsandbytes")
    print("pip install -r requirements.txt")
    print("python setup.py install")
    
    print("\n方案 3: 使用不带量化的训练脚本（最稳定）")
    print("---------------------------------------")
    print("python finetune_qwen_no_quant.py --batch_size 1 --max_length 512")
    print("\n这个方案不使用 bitsandbytes，但需要更多显存")
    print("对于 Qwen2-1.5B，大约需要 8-12GB 显存")
    
    print("\n方案 4: 使用 DeepSpeed ZeRO")
    print("---------------------------------------")
    print("pip install deepspeed")
    print("然后使用 DeepSpeed 配置文件训练")

print("\n" + "=" * 60)
print("显存需求估算")
print("=" * 60)
print("\nQwen2-1.5B 模型:")
print("- 不使用量化: ~8-12GB")
print("- 8-bit 量化: ~4-6GB")
print("- 4-bit 量化: ~3-4GB")
print("\n如果你的显存不足，考虑:")
print("1. 使用更小的模型（如 Qwen2-0.5B）")
print("2. 减小 batch_size 到 1")
print("3. 减小 max_length 到 256")
print("4. 减小 lora_r 到 32")
