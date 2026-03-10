"""测试相关度显示"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main_new import NewCardGameJudge

print("=" * 80)
print("测试相关度显示")
print("=" * 80)

# 初始化裁判系统
print("\n初始化系统...")
judge = NewCardGameJudge()

# 测试问题
test_questions = [
    "介绍一下数码兽攻击的流程",
    "进化时费用会退还吗",
    "安防效果和其他效果同时触发时的顺序",
]

for i, question in enumerate(test_questions, 1):
    print("\n" + "=" * 80)
    print(f"测试 {i}: {question}")
    print("=" * 80)
    
    # 查询（verbose=True 会显示详细的相关度信息）
    result = judge.query(question, top_k=5, verbose=True)
    
    print("\n" + "-" * 80)
    print("【统计】")
    print(f"  记忆: {result['memories_used']} 条")
    print(f"  卡牌: {result['cards_found']} 张")
    print(f"  规则/裁定: {result['sources_used']} 条")
    print(f"  耗时: {result['elapsed_time']:.2f}s")
    print("-" * 80)
    
    if i < len(test_questions):
        input("\n按回车继续下一个测试...")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
print("\n说明:")
print("  相关度条形图: █████████░ (0.0 - 1.0)")
print("  - 10个方块，每个代表10%")
print("  - █ = 已填充")
print("  - ░ = 未填充")
print("  - 分数越高，相关度越高")
