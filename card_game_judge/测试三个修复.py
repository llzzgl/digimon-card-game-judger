"""
测试三个修复：
1. FEEDBACK.md 自动更新
2. EX8-074 等卡牌编号正确提取
3. 控制台显示相关性数值
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("测试三个修复")
print("=" * 80)

# 测试 1: 卡牌编号提取
print("\n【测试 1】卡牌编号提取")
print("-" * 80)

from app.query_processor import query_processor

test_query = "我方回合，对面场上有EX8-074，我方进化EX11-024，发动进化效果登场P-165"
print(f"测试问题: {test_query}")

extracted_cards = query_processor.extract_card_numbers(test_query)
print(f"\n提取到的卡牌编号: {extracted_cards}")

expected_cards = ["EX08-074", "EX11-024", "P-165"]
if extracted_cards == expected_cards:
    print("✅ 测试通过：卡牌编号提取正确")
else:
    print(f"❌ 测试失败：期望 {expected_cards}，实际 {extracted_cards}")

# 测试 2: 相关性数值显示（通过实际查询测试）
print("\n【测试 2】相关性数值显示")
print("-" * 80)
print("将通过实际查询测试，请查看控制台输出中是否有相关度数值...")

from main_new import NewCardGameJudge

judge = NewCardGameJudge()

# 执行查询，verbose=True 会显示详细信息包括相关度
test_question = "攻击流程是什么顺序？"
print(f"\n测试问题: {test_question}")
print("\n查询结果：")
print("=" * 80)

result = judge.query(test_question, top_k=3, verbose=True)

print("\n" + "=" * 80)
print("✅ 如果上面的输出中看到 '相关度: X.XXXX (XX.X%)' 格式，则测试通过")

# 测试 3: FEEDBACK.md 自动更新
print("\n【测试 3】FEEDBACK.md 自动更新")
print("-" * 80)

# 读取当前 FEEDBACK.md 内容
feedback_path = Path(".judge/FEEDBACK.md")
if feedback_path.exists():
    with open(feedback_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    original_length = len(original_content)
    print(f"原始 FEEDBACK.md 长度: {original_length} 字符")
else:
    print("❌ FEEDBACK.md 不存在")
    original_content = ""
    original_length = 0

# 测试保存修正（会自动更新 FEEDBACK.md）
print("\n测试保存修正记忆...")
correction_result = judge.save_correction(
    question="测试问题：进化时费用会退还吗？",
    wrong_answer="费用会退还到记忆区",
    correct_answer="根据综合规则8.1，进化费用不会退还",
    user_explanation="这是测试修正功能",
    importance=3
)

if correction_result['success']:
    print(f"✅ 修正记忆保存成功")
    print(f"   记忆ID: {correction_result['memory_id']}")
    print(f"   FEEDBACK.md 更新: {'成功' if correction_result.get('feedback_saved') else '失败'}")
    
    # 验证 FEEDBACK.md 是否真的更新了
    if feedback_path.exists():
        with open(feedback_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        new_length = len(new_content)
        
        if new_length > original_length:
            print(f"✅ FEEDBACK.md 已更新（新增 {new_length - original_length} 字符）")
            
            # 显示新增的内容（最后500字符）
            print("\n新增内容预览：")
            print("-" * 80)
            print(new_content[-500:])
        else:
            print(f"❌ FEEDBACK.md 未更新（长度未变化）")
    else:
        print("❌ FEEDBACK.md 不存在")
else:
    print(f"❌ 修正记忆保存失败: {correction_result.get('error')}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

print("\n📋 测试总结：")
print("1. 卡牌编号提取：检查上面的测试结果")
print("2. 相关性数值显示：检查查询输出中是否有 '相关度: X.XXXX (XX.X%)' 格式")
print("3. FEEDBACK.md 更新：检查文件是否新增了反馈记录")
