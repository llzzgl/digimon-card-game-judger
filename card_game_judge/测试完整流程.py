"""测试完整的查询流程，包括卡牌提取"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("测试完整查询流程")
print("=" * 80)

from main_new import NewCardGameJudge

print("\n初始化系统...")
judge = NewCardGameJudge()

print("\n" + "=" * 80)
print("测试问题：我方回合，对面场上有EX8-074，我方进化EX11-024，发动进化效果登场P-165")
print("=" * 80)

test_question = "我方回合，对面场上有EX8-074，我方进化EX11-024，发动进化效果登场P-165，此时EX8-074的效果先处理还是EX11-024的另一个进化时效果先处理。"

result = judge.query(test_question, top_k=3, verbose=True)

print("\n" + "=" * 80)
print("【裁判回答】")
print("=" * 80)
print(result['answer'])

print("\n" + "=" * 80)
print("【统计信息】")
print("=" * 80)
print(f"使用记忆: {result['memories_used']} 条")
print(f"卡牌效果: {result['cards_found']} 张")
print(f"规则/裁定: {result['sources_used']} 条")
print(f"耗时: {result['elapsed_time']:.2f}s")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
