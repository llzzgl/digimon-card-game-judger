#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试微调模型
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def test_model_loading():
    """测试模型加载"""
    print("=" * 60)
    print("测试微调模型加载")
    print("=" * 60)
    
    try:
        from app.llm_service_finetuned import get_finetuned_llm_service
        
        print("\n📥 正在加载微调模型...")
        service = get_finetuned_llm_service()
        print("✅ 模型加载成功！\n")
        
        return service
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_card_query(service):
    """测试卡牌查询"""
    print("=" * 60)
    print("测试 1: 卡牌查询")
    print("=" * 60)
    
    question = "EX11-026 是什么卡？请提供详细信息。"
    print(f"\n问题: {question}\n")
    
    try:
        # 模拟空上下文（直接测试模型知识）
        answer = service.generate_answer(question, [])
        print(f"回答:\n{answer}\n")
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_rule_query(service):
    """测试规则查询"""
    print("=" * 60)
    print("测试 2: 规则查询")
    print("=" * 60)
    
    question = "≪贯通≫效果在什么时候触发？如何处理？"
    print(f"\n问题: {question}\n")
    
    try:
        answer = service.generate_answer(question, [])
        print(f"回答:\n{answer}\n")
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_with_context(service):
    """测试带上下文的查询"""
    print("=" * 60)
    print("测试 3: 带上下文查询")
    print("=" * 60)
    
    question = "数码合体可以不放置任何卡牌吗？"
    context_docs = [
        {
            "content": "数码合体是登场时的特殊规则。如果宣言了数码合体，则必须至少选择1张卡牌置于下方。但数码合体本身不是强制的，可以选择不进行数码合体直接登场。",
            "metadata": {"title": "数码合体规则"},
            "doc_type": "rule"
        }
    ]
    
    print(f"\n问题: {question}")
    print(f"上下文: {len(context_docs)} 个参考文档\n")
    
    try:
        answer = service.generate_answer(question, context_docs)
        print(f"回答:\n{answer}\n")
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def main():
    """主函数"""
    print("\n🎯 微调模型测试工具\n")
    
    # 测试 1: 加载模型
    service = test_model_loading()
    if service is None:
        print("\n❌ 模型加载失败，无法继续测试")
        return
    
    # 测试 2: 卡牌查询
    test_card_query(service)
    
    # 测试 3: 规则查询
    test_rule_query(service)
    
    # 测试 4: 带上下文查询
    test_with_context(service)
    
    print("=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n💡 提示:")
    print("   1. 如果回答质量不理想，可以调整训练参数重新微调")
    print("   2. 可以在 .env 中设置 LLM_MODEL=finetuned 来使用微调模型")
    print("   3. 查看 USE_FINETUNED_MODEL.md 了解更多使用方法")


if __name__ == "__main__":
    main()
