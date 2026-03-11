#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试卡牌编号提取和数据获取
"""
import sys
import os

# 设置环境
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

sys.path.insert(0, os.path.dirname(__file__))

from app.query_processor import query_processor
from app.rag import RAGManager, create_embedding_provider


def test_card_number_extraction():
    """测试卡牌编号提取"""
    print("=" * 60)
    print("测试1: 卡牌编号提取")
    print("=" * 60)
    
    test_question = "我方联展了bt23-032土偶兽，把对方的数码兽退化成bt24-016拉米亚兽，并选择其主要阶段开始时攻击，土偶进化源中有bt23-027天使兽和bt23-050甲龙兽。对方拉米亚进化源中有bt21-001基基兽。"
    
    print(f"\n问题: {test_question[:80]}...")
    
    card_numbers = query_processor.extract_card_numbers(test_question)
    
    print(f"\n提取到的卡牌编号: {card_numbers}")
    print(f"数量: {len(card_numbers)}")
    
    return card_numbers


def test_card_data_retrieval(card_numbers):
    """测试卡牌数据获取"""
    print("\n" + "=" * 60)
    print("测试2: 卡牌数据获取")
    print("=" * 60)
    
    # 初始化RAG管理器
    print("\n初始化RAG管理器...")
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    print(f"\n卡牌缓存数量: {len(rag._card_cache)}")
    
    # 测试每张卡牌
    found_count = 0
    for card_no in card_numbers:
        print(f"\n查询: {card_no}")
        card_data = rag.search_card_by_number(card_no)
        
        if card_data:
            found_count += 1
            print(f"  ✅ 找到")
            print(f"  名称: {card_data.get('name_cn', card_data.get('name_jp', '未知'))}")
            print(f"  类型: {card_data.get('type', '未知')}")
            
            # 显示效果前100字符
            effect = card_data.get('effect_cn', card_data.get('effect_jp', ''))
            if effect:
                print(f"  效果: {effect[:100]}...")
        else:
            print(f"  ❌ 未找到")
    
    print(f"\n总结: 找到 {found_count}/{len(card_numbers)} 张卡牌")
    
    return found_count > 0


def test_card_formatting():
    """测试卡牌格式化"""
    print("\n" + "=" * 60)
    print("测试3: 卡牌格式化")
    print("=" * 60)
    
    # 初始化RAG管理器
    rag = RAGManager(
        persist_dir="data/rag_store",
        embedding_provider=create_embedding_provider("local")
    )
    
    # 测试一张卡牌
    test_card_no = "BT23-032"
    print(f"\n测试卡牌: {test_card_no}")
    
    card_data = rag.search_card_by_number(test_card_no)
    
    if card_data:
        print("\n原始数据字段:")
        for key in card_data.keys():
            print(f"  - {key}")
        
        print("\n格式化后的内容:")
        print("-" * 60)
        
        # 模拟格式化
        lines = []
        if 'card_no' in card_data:
            lines.append(f"卡牌编号: {card_data['card_no']}")
        if 'name_cn' in card_data:
            lines.append(f"中文名: {card_data['name_cn']}")
        if 'effect_cn' in card_data:
            lines.append(f"\n效果:\n{card_data['effect_cn']}")
        
        formatted = "\n".join(lines)
        print(formatted)
        print("-" * 60)
    else:
        print(f"  ❌ 未找到卡牌 {test_card_no}")


def main():
    """主测试函数"""
    print("🎴 测试卡牌提取和数据获取")
    print("=" * 60)
    
    try:
        # 测试1: 提取卡牌编号
        card_numbers = test_card_number_extraction()
        
        if not card_numbers:
            print("\n❌ 未提取到卡牌编号，测试终止")
            return
        
        # 测试2: 获取卡牌数据
        has_data = test_card_data_retrieval(card_numbers)
        
        if not has_data:
            print("\n⚠️  警告: 卡牌数据库可能为空")
            print("   请先导入卡牌数据:")
            print("   python import_data.py --import-cards")
            return
        
        # 测试3: 格式化
        test_card_formatting()
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
