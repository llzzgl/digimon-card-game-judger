"""测试修正功能"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main_new import NewCardGameJudge

print("=" * 80)
print("测试修正功能")
print("=" * 80)

# 初始化裁判系统
print("\n初始化系统...")
judge = NewCardGameJudge()

# 测试1: 查看卡牌信息格式化
print("\n" + "=" * 80)
print("测试1: 卡牌信息完整化")
print("=" * 80)

card_no = "BT23-032"
card_data = judge.search_card(card_no)

if card_data:
    print(f"\n原始卡牌数据字段: {list(card_data.keys())}")
    print(f"\n格式化后的卡牌信息:")
    print("-" * 80)
    formatted = judge._format_card_content(card_data)
    print(formatted)
    print("-" * 80)
else:
    print(f"未找到卡牌: {card_no}")

# 测试2: 修正功能
print("\n" + "=" * 80)
print("测试2: 修正功能")
print("=" * 80)

test_question = "进化时费用会退还吗？"
test_wrong_answer = "进化时支付的费用会退还到内存区域。"
test_correct_answer = "进化时支付的费用不会退还。进化费用是从手牌进化到场上数码兽时需要支付的费用，这个费用支付后不会返还。"
test_explanation = "根据综合规则，进化费用是进化的成本，支付后不返还。这与登场费用的处理方式相同。"

print(f"\n问题: {test_question}")
print(f"\n错误答案: {test_wrong_answer}")
print(f"\n正确答案: {test_correct_answer}")
print(f"\n用户说明: {test_explanation}")

print("\n正在保存修正记忆...")
result = judge.save_correction(
    question=test_question,
    wrong_answer=test_wrong_answer,
    correct_answer=test_correct_answer,
    user_explanation=test_explanation,
    importance=3
)

if result['success']:
    print("\n✅ 修正记忆保存成功！")
    print(f"\n记忆ID: {result['memory_id']}")
    print(f"\n知识规律总结:")
    print("-" * 80)
    print(result['summary'])
    print("-" * 80)
else:
    print(f"\n❌ 保存失败: {result.get('error')}")

# 测试3: 搜索修正记忆
print("\n" + "=" * 80)
print("测试3: 搜索修正记忆")
print("=" * 80)

print("\n搜索相关记忆...")
memories = judge.memory.search_memories(test_question, top_k=3)

if memories:
    print(f"\n找到 {len(memories)} 条相关记忆:")
    for i, mem in enumerate(memories, 1):
        print(f"\n记忆 {i}:")
        print(f"  问题: {mem['question']}")
        print(f"  相似度: {mem['similarity']:.2%}")
        print(f"  重要性: {'⭐' * mem['importance']}")
        print(f"  用户确认: {'✅' if mem['user_confirmed'] else '❓'}")
        if mem.get('metadata', {}).get('is_correction'):
            print(f"  类型: 🔧 修正记忆")
        print(f"  总结: {mem['summary'][:100]}...")
else:
    print("\n未找到相关记忆")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
