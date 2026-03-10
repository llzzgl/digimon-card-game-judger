#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本 - 检查服务启动问题
"""
import os
import sys
from pathlib import Path

def check_env():
    """检查环境配置"""
    print("=" * 60)
    print("1. 检查环境配置")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_model = os.getenv("LLM_MODEL", "qwen")
    print(f"✅ LLM_MODEL = {llm_model}")
    
    if llm_model == "finetuned":
        lora_path = os.getenv("FINETUNED_LORA_PATH", "")
        base_model = os.getenv("FINETUNED_BASE_MODEL", "")
        print(f"   FINETUNED_LORA_PATH = {lora_path}")
        print(f"   FINETUNED_BASE_MODEL = {base_model}")
        
        # 检查文件是否存在
        if lora_path and lora_path.strip():
            lora_exists = Path(lora_path).exists()
            print(f"   LoRA 文件存在: {'✅' if lora_exists else '❌'}")
        
        if base_model and not base_model.startswith("Qwen/"):
            base_exists = Path(base_model).exists()
            print(f"   基础模型存在: {'✅' if base_exists else '❌'}")
    
    return llm_model


def check_dependencies():
    """检查依赖库"""
    print("\n" + "=" * 60)
    print("2. 检查依赖库")
    print("=" * 60)
    
    required = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "langchain": "LangChain",
        "chromadb": "ChromaDB",
    }
    
    optional = {
        "peft": "PEFT (微调模型)",
        "transformers": "Transformers (微调模型)",
        "torch": "PyTorch (微调模型)",
    }
    
    print("\n必需库:")
    for module, name in required.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - 未安装")
    
    print("\n可选库 (使用微调模型时需要):")
    for module, name in optional.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"⚠️  {name} - 未安装")


def check_model_loading(llm_model):
    """检查模型加载"""
    print("\n" + "=" * 60)
    print("3. 检查模型加载")
    print("=" * 60)
    
    try:
        if llm_model == "finetuned":
            print("\n尝试加载微调模型...")
            from app.llm_service_finetuned import get_finetuned_llm_service
            
            lora_path = os.getenv("FINETUNED_LORA_PATH", "finetune/output/dtcg_qwen_lora")
            base_model = os.getenv("FINETUNED_BASE_MODEL", "Qwen/Qwen2-1.5B-Instruct")
            
            service = get_finetuned_llm_service(lora_path=lora_path, base_model=base_model)
            print("✅ 微调模型加载成功")
            return True
        else:
            print(f"\n尝试加载 {llm_model} 模型...")
            from app.llm_service import LLMService
            service = LLMService()
            print(f"✅ {llm_model} 模型加载成功")
            return True
            
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_api():
    """检查 API 模块"""
    print("\n" + "=" * 60)
    print("4. 检查 API 模块")
    print("=" * 60)
    
    try:
        print("\n尝试导入 API 模块...")
        from app.api import app
        print("✅ API 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ API 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def suggest_fix(llm_model, model_ok, api_ok):
    """建议修复方案"""
    print("\n" + "=" * 60)
    print("5. 修复建议")
    print("=" * 60)
    
    if not model_ok:
        if llm_model == "finetuned":
            print("\n❌ 微调模型加载失败")
            print("\n推荐方案:")
            print("  1. 合并 LoRA 权重:")
            print("     python merge_lora.py")
            print("     然后修改 .env:")
            print("     FINETUNED_BASE_MODEL=finetune/output/dtcg_qwen_merged")
            print("     FINETUNED_LORA_PATH=")
            print("\n  2. 或切换到 API 模型:")
            print("     修改 .env: LLM_MODEL=qwen")
        else:
            print(f"\n❌ {llm_model} 模型加载失败")
            print("\n请检查:")
            print("  - API Key 是否正确")
            print("  - 网络连接是否正常")
            print("  - 代理设置是否正确")
    
    if not api_ok:
        print("\n❌ API 模块加载失败")
        print("\n可能原因:")
        print("  - 依赖库未安装")
        print("  - 代码语法错误")
        print("  - 模型加载失败导致")


def main():
    """主函数"""
    print("\n🔍 DTCG 裁判助手 - 诊断工具\n")
    
    # 1. 检查环境
    llm_model = check_env()
    
    # 2. 检查依赖
    check_dependencies()
    
    # 3. 检查模型加载
    model_ok = check_model_loading(llm_model)
    
    # 4. 检查 API
    api_ok = check_api()
    
    # 5. 建议修复
    suggest_fix(llm_model, model_ok, api_ok)
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    if model_ok and api_ok:
        print("\n✅ 所有检查通过！")
        print("\n可以正常启动服务:")
        print("  python main.py")
    else:
        print("\n❌ 发现问题，请按照上述建议修复")
        print("\n快速修复:")
        print("  1. 如果是微调模型问题: python merge_lora.py")
        print("  2. 如果是依赖问题: pip install -r requirements.txt")
        print("  3. 临时方案: 修改 .env 中 LLM_MODEL=qwen")


if __name__ == "__main__":
    main()
