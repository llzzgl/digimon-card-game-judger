#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试记忆系统功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.memory_manager import memory_manager
from app.memory_summarizer import memory_summarizer
from app.memory_config import MemoryType, MemoryImportance


def test_basic_memory():
    """测试基本记忆功能"""
    print("=" * 60)
    print("测试1: 基本记忆功能")
    print("=" * 60)
    
    # 测试问答对
    question = "BT01-001的登场时效果能否触发？"
    answer = """根据规则，BT01-001的登场时效果可以触发。

【规则依据】
- 登场时效果在数码兽从手牌或其他区域登场到战斗区或育成区时触发
- 效果触发后，按照回合玩家优先的原则处理

【注意事项】
- 如果登场被无效，则登场时效果不会触发
- 多个登场时效果同时触发时，回合玩家的效果优先处理"""
    
    # 生成总结
    print("\n📝 生成总结...")
    summary = memory_summarizer.summarize(question, answer, ["BT01-001"])
    print(f"总结:\n{summary}\n")
    
    # 保存记忆
    print("💾 保存记忆...")
    memory = memory_manager.add_memory(
        question=question,
        answer=answer,
        summary=summary,
        memory_type=MemoryType.LONG_TERM,
        importance=MemoryImportance.HIGH,
        card_numbers=["BT01-001"],
        tags=["登场时效果", "触发时机"],
        user_confirmed=True
    )
    
    print(f"✅ 记忆已保存: {memory.id}")
    return memory.id


def test_memory_search():
    """测试记忆搜索"""
    print("\n" + "=" * 60)
    print("测试2: 记忆搜索")
    print("=" * 60)
    
    # 搜索相关记忆
    queries = [
        "BT01-001效果",
        "登场时效果触发",
        "卡牌效果时机"
    ]
    
    for query in queries:
        print(f"\n🔍 搜索: {query}")
        results = memory_manager.search_memories(query, top_k=3)
        
        if results:
            print(f"找到 {len(results)} 条记忆:")
            for i, mem in enumerate(results, 1):
                print(f"\n  {i}. 相似度: {mem['similarity']:.2%}")
                print(f"     问题: {mem['question'][:50]}...")
                print(f"     已验证: {'✅' if mem['user_confirmed'] else '❌'}")
        else:
            print("  未找到相关记忆")


def test_memory_feedback():
    """测试记忆反馈"""
    print("\n" + "=" * 60)
    print("测试3: 记忆反馈")
    print("=" * 60)
    
    # 获取第一条记忆
    stats = memory_manager.get_statistics()
    if stats['total_memories'] == 0:
        print("⚠️  没有记忆可测试")
        return
    
    # 搜索一条记忆
    results = memory_manager.search_memories("BT01-001", top_k=1)
    if not results:
        print("⚠️  未找到测试记忆")
        return
    
    memory_id = results[0]['id']
    print(f"📝 更新记忆反馈: {memory_id}")
    
    # 更新反馈
    success = memory_manager.update_memory_feedback(
        memory_id=memory_id,
        user_confirmed=True,
        user_feedback="测试反馈：答案准确，解释清晰"
    )
    
    if success:
        print("✅ 反馈更新成功")
        
        # 获取完整记忆
        memory = memory_manager.get_memory(memory_id)
        if memory:
            print(f"   用户确认: {memory['user_confirmed']}")
            print(f"   用户反馈: {memory.get('user_feedback', '无')}")
    else:
        print("❌ 反馈更新失败")


def test_memory_statistics():
    """测试记忆统计"""
    print("\n" + "=" * 60)
    print("测试4: 记忆统计")
    print("=" * 60)
    
    stats = memory_manager.get_statistics()
    
    print(f"📊 记忆统计:")
    print(f"   总记忆数: {stats['total_memories']}")
    print(f"   短期记忆: {stats['short_term_memories']}")
    print(f"   存储路径: {stats['storage_path']}")
    print(f"   最后更新: {stats.get('last_updated', '未知')}")
    print(f"\n⚙️  配置:")
    for key, value in stats['config'].items():
        print(f"   {key}: {value}")


def test_batch_memories():
    """测试批量添加记忆"""
    print("\n" + "=" * 60)
    print("测试5: 批量添加记忆")
    print("=" * 60)
    
    test_cases = [
        {
            "question": "反击效果可以在对方回合使用吗？",
            "answer": "是的，反击效果可以在对方回合使用。反击是一种特殊的效果类型，可以在对方攻击时发动。",
            "tags": ["反击", "时机"],
            "importance": MemoryImportance.HIGH
        },
        {
            "question": "两张卡牌同时触发效果时如何处理？",
            "answer": "根据回合玩家优先原则，回合玩家的效果先处理，然后是非回合玩家的效果。",
            "tags": ["效果处理", "优先级"],
            "importance": MemoryImportance.CRITICAL
        },
        {
            "question": "进化源的效果何时生效？",
            "answer": "进化源的效果在卡牌作为进化源时持续生效，除非效果文本另有说明。",
            "tags": ["进化源", "持续效果"],
            "importance": MemoryImportance.MEDIUM
        }
    ]
    
    print(f"📝 批量添加 {len(test_cases)} 条记忆...")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n  {i}/{len(test_cases)}: {case['question'][:30]}...")
        
        # 生成总结
        summary = memory_summarizer.summarize(
            case['question'],
            case['answer']
        )
        
        # 保存记忆
        memory = memory_manager.add_memory(
            question=case['question'],
            answer=case['answer'],
            summary=summary,
            memory_type=MemoryType.LONG_TERM,
            importance=case['importance'],
            tags=case['tags'],
            user_confirmed=True
        )
        
        print(f"     ✅ 已保存: {memory.id}")
    
    print(f"\n✅ 批量添加完成")


def main():
    """主测试函数"""
    print("🧠 记忆系统测试")
    print("=" * 60)
    
    try:
        # 测试1: 基本功能
        memory_id = test_basic_memory()
        
        # 测试2: 搜索
        test_memory_search()
        
        # 测试3: 反馈
        test_memory_feedback()
        
        # 测试4: 统计
        test_memory_statistics()
        
        # 测试5: 批量添加
        test_batch_memories()
        
        # 最终统计
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
        final_stats = memory_manager.get_statistics()
        print(f"最终记忆数: {final_stats['total_memories']}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
