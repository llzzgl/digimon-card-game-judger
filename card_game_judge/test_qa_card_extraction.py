"""测试从QA中提取卡牌编号功能"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main_new import NewCardGameJudge

print("=" * 80)
print("测试从QA中提取卡牌编号功能")
print("=" * 80)

# 初始化裁判系统
print("\n初始化系统...")
judge = NewCardGameJudge()

# 测试问题：不包含卡牌编号，但相关的QA中会包含
test_questions = [
    # 测试1: 包含卡牌编号的问题
    {
        "question": "我方联展了bt23-032土偶兽，把对方的数码兽退化成bt24-016拉米亚兽",
        "description": "用户问题中包含卡牌编号"
    },
    # 测试2: 不包含卡牌编号，但QA中会有
    {
        "question": "安防效果和其他效果同时触发时的顺序是什么？",
        "description": "用户问题不含卡牌编号，但相关QA可能包含"
    },
    # 测试3: 涉及特定机制
    {
        "question": "马尔斯兽可以攻击休眠状态的数码兽吗？",
        "description": "提到特定卡牌名称，QA中应该有BT8-018"
    },
]

for i, test in enumerate(test_questions, 1):
    question = test["question"]
    description = test["description"]
    
    print("\n" + "=" * 80)
    print(f"测试 {i}: {description}")
    print(f"问题: {question}")
    print("=" * 80)
    
    result = judge.query(question, top_k=3, verbose=True)
    
    print("\n" + "-" * 80)
    print("【统计信息】")
    print(f"  使用记忆: {result['memories_used']} 条")
    print(f"  卡牌效果: {result['cards_found']} 张")
    print(f"    - 来自用户问题: ?")
    print(f"    - 来自QA引用: ?")
    print(f"  规则/裁定: {result['sources_used']} 条")
    print(f"  耗时: {result['elapsed_time']:.2f}s")
    print("-" * 80)
    
    # 只显示答案的前300字符
    answer_preview = result['answer'][:300] + "..." if len(result['answer']) > 300 else result['answer']
    print(f"\n【答案预览】\n{answer_preview}")
    
    if i < len(test_questions):
        print("\n" + "=" * 80)
        input("按回车继续下一个测试...")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
print("\n说明:")
print("- 步骤1: 从用户问题中提取卡牌编号")
print("- 步骤2: 检索相关的规则和裁定")
print("- 步骤3: 从检索到的QA内容中提取卡牌编号")
print("- 所有卡牌信息都不计入top_k限制")

