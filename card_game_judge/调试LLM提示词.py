"""
调试LLM提示词 - 查看实际传给LLM的完整内容
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("调试LLM提示词")
print("=" * 80)

# 模拟参考资料
mock_context = """【参考1】
来源：数码宝贝卡牌对战_综合规则3.1（规则）
内容：家进行。11-1-3. 攻击按以下顺序进行各时机："攻击宣言"、"反击时机"、"阻挡时机"、"成立确认"、"攻击结束时"。11-1-4. 各时机在其中需要结算的处理全部消失之前，不会进行到下一个时机。11-1-5. 宣言攻击后，将进行之后的所有时机。### 11-2 攻击宣言11-2-1. 回合玩家可以将自己战斗区中的数码宝贝休眠，并宣言攻击。11-2-2. 同时宣言攻击，并选择攻击目标。11-2-3. 攻击宣言，每次攻击只能进行1只。不能同时使多只数码宝贝攻击。"""

mock_question = "攻击流程是什么顺序？"

print("\n【步骤1】查看SYSTEM_PROMPT")
print("-" * 80)

try:
    from app.llm_service import SYSTEM_PROMPT, USER_PROMPT
    
    print("SYSTEM_PROMPT内容：")
    print(SYSTEM_PROMPT)
    print("\nUSER_PROMPT内容：")
    print(USER_PROMPT)
    
except Exception as e:
    print(f"✗ 加载失败: {e}")

print("\n【步骤2】查看配置系统提示词")
print("-" * 80)

try:
    from app.judge_config_loader import get_system_prompt
    
    config_prompt = get_system_prompt()
    print("配置系统提示词内容：")
    print(config_prompt)
    
except Exception as e:
    print(f"✗ 加载失败: {e}")

print("\n【步骤3】模拟合并后的提示词")
print("-" * 80)

try:
    from app.judge_config_loader import get_system_prompt
    from app.llm_service import SYSTEM_PROMPT, USER_PROMPT
    
    config_prompt = get_system_prompt()
    
    # 模拟合并
    combined_prompt = f"""{config_prompt}

---

{SYSTEM_PROMPT}"""
    
    print("合并后的系统提示词：")
    print(combined_prompt)
    
    # 替换context占位符
    final_system_prompt = combined_prompt.replace("{context}", mock_context)
    
    print("\n" + "=" * 80)
    print("【最终传给LLM的系统提示词】")
    print("=" * 80)
    print(final_system_prompt)
    
    # 用户提示词
    final_user_prompt = USER_PROMPT.replace("{question}", mock_question)
    
    print("\n" + "=" * 80)
    print("【最终传给LLM的用户提示词】")
    print("=" * 80)
    print(final_user_prompt)
    
    print("\n" + "=" * 80)
    print("【分析】")
    print("=" * 80)
    
    # 检查关键内容
    checks = {
        "包含规则11-1-3": "11-1-3" in final_system_prompt,
        "包含攻击时机": "攻击宣言" in final_system_prompt and "反击时机" in final_system_prompt,
        "包含'必须使用'": "必须" in final_system_prompt,
        "包含'引用规则编号'": "引用" in final_system_prompt and "规则编号" in final_system_prompt,
    }
    
    print("\n关键内容检查：")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n✓ 提示词包含所有必要内容")
        print("\n⚠️ 如果LLM仍然说'未找到'，可能是：")
        print("  1. LLM模型本身的问题（理解能力不足）")
        print("  2. 参考资料格式不够清晰")
        print("  3. 提示词过长，LLM注意力不集中")
    else:
        print("\n✗ 提示词缺少某些关键内容")
    
except Exception as e:
    print(f"✗ 模拟失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("【建议】")
print("=" * 80)

print("""
如果提示词包含所有必要内容，但LLM仍然说"未找到"，可以尝试：

1. 简化参考资料格式
   - 使用更清晰的标记
   - 突出显示规则编号
   - 减少无关内容

2. 强化提示词
   - 在SYSTEM_PROMPT开头就强调"参考资料中包含答案"
   - 使用更强的语气（"必须"、"一定"）
   - 给出具体的例子

3. 调整LLM参数
   - 降低temperature（更确定性）
   - 增加max_tokens（允许更长的回答）

4. 尝试不同的提示词结构
   - 将参考资料放在问题之后
   - 使用XML标签明确标记
   - 使用编号列表格式
""")

print("=" * 80)
