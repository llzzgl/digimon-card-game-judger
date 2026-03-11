#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 main_new.py 的记忆功能集成
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

from main_new import NewCardGameJudge


def test_basic_query():
    """测试基本查询功能"""
    print("=" * 60)
    print("测试1: 基本查询功能")
    print("=" * 60)
    
    judge = NewCardGameJudge()
    
    question = "进化时费用会退还吗？"
    print(f"\n问题: {question}")
    
    result = judge.query(question, verbose=False)
    
    print(f"\n答案: {result['answer'][:200]}...")
    print(f"\n统计:")
    print(f"  使用记忆: {result['memories_used']} 条")
    print(f"  使用来源: {result['sources_used']} 条")
    print(f"  耗时: {result['elapsed_time']:.2f}s")
    
    return judge, question, result['answer']


def test_save_memory(judge, question, answer):
    """测试保存记忆功能"""
    print("\n" + "=" * 60)
    print("测试2: 保存记忆功能")
    print("=" * 60)
    
    print(f"\n保存问答为记忆...")
    result = judge.save_as_memory(
        question=question,
        answer=answer,
        user_confirmed=True,
        importance=3,
        tags=["进化", "费用"]
    )
    
    if result['success']:
        print(f"✅ 保存成功")
        print(f"   记忆ID: {result['memory_id']}")
        print(f"   总结: {result['summary'][:100]}...")
        return result['memory_id']
    else:
        print(f"❌ 保存失败: {result['error']}")
        return None


def test_memory_search(judge, question):
    """测试记忆搜索功能"""
    print("\n" + "=" * 60)
    print("测试3: 记忆搜索功能")
    print("=" * 60)
    
    print(f"\n搜索相关记忆: {question}")
    memories = judge.memory.search_memories(question, top_k=3)
    
    if memories:
        print(f"\n找到 {len(memories)} 条记忆:")
        for i, mem in enumerate(memories, 1):
            status = "✅" if mem['user_confirmed'] else "❓"
            print(f"\n  {i}. {status} {mem['question']}")
            print(f"     相似度: {mem['similarity']:.2%}")
            print(f"     重要性: {'⭐' * mem['importance']}")
            print(f"     总结: {mem['summary'][:80]}...")
    else:
        print("\n未找到相关记忆")


def test_query_with_memory(judge):
    """测试使用记忆的查询"""
    print("\n" + "=" * 60)
    print("测试4: 使用记忆的查询")
    print("=" * 60)
    
    # 查询相似问题
    similar_question = "进化的时候需要支付费用吗？"
    print(f"\n问题: {similar_question}")
    
    result = judge.query(similar_question, verbose=False)
    
    print(f"\n答案: {result['answer'][:200]}...")
    print(f"\n统计:")
    print(f"  使用记忆: {result['memories_used']} 条")
    print(f"  使用来源: {result['sources_used']} 条")
    print(f"  耗时: {result['elapsed_time']:.2f}s")
    
    if result['memories_used'] > 0:
        print("\n✅ 成功使用记忆加速查询！")
    else:
        print("\n⚠️  未使用记忆（可能相似度不够）")


def test_memory_stats(judge):
    """测试记忆统计"""
    print("\n" + "=" * 60)
    print("测试5: 记忆统计")
    print("=" * 60)
    
    stats = judge.memory.get_statistics()
    
    print(f"\n📊 记忆统计:")
    print(f"   总记忆数: {stats['total_memories']}")
    print(f"   短期记忆: {stats['short_term_memories']}")
    print(f"   存储路径: {stats['storage_path']}")
    
    print(f"\n⚙️  配置:")
    for key, value in stats['config'].items():
        print(f"   {key}: {value}")


def main():
    """主测试函数"""
    print("🧠 测试 main_new.py 记忆功能集成")
    print("=" * 60)
    
    try:
        # 测试1: 基本查询
        judge, question, answer = test_basic_query()
        
        # 测试2: 保存记忆
        memory_id = test_save_memory(judge, question, answer)
        
        # 测试3: 搜索记忆
        test_memory_search(judge, question)
        
        # 测试4: 使用记忆查询
        test_query_with_memory(judge)
        
        # 测试5: 统计信息
        test_memory_stats(judge)
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
        final_stats = judge.memory.get_statistics()
        print(f"\n最终记忆数: {final_stats['total_memories']}")
        print(f"\n💡 提示: 运行 'python main_new.py' 启动Web界面")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
