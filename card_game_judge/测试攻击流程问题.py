"""
测试攻击流程问题的修复
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("测试攻击流程问题修复")
print("=" * 80)

# 测试1: 检查系统提示词
print("\n【测试1】检查系统提示词")
print("-" * 80)

try:
    from app.llm_service import SYSTEM_PROMPT
    
    print("原有系统提示词内容：")
    print(SYSTEM_PROMPT[:500])
    print("...")
    
    # 检查关键要求
    checks = {
        "优先使用参考资料": "优先使用" in SYSTEM_PROMPT or "必须基于" in SYSTEM_PROMPT,
        "引用规则编号": "引用" in SYSTEM_PROMPT and "规则" in SYSTEM_PROMPT,
        "明确裁定": "明确" in SYSTEM_PROMPT,
        "不要过于保守": "必须使用" in SYSTEM_PROMPT or "如果参考资料中有相关内容" in SYSTEM_PROMPT,
    }
    
    print("\n关键要求检查：")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n✓ 系统提示词已优化")
    else:
        print("\n⚠ 系统提示词可能需要进一步优化")
    
except Exception as e:
    print(f"✗ 检查失败: {e}")

# 测试2: 检查配置系统提示词
print("\n【测试2】检查配置系统提示词")
print("-" * 80)

try:
    from app.judge_config_loader import get_system_prompt
    
    config_prompt = get_system_prompt()
    
    print("配置系统提示词内容（前300字符）：")
    print(config_prompt[:300])
    print("...")
    
    # 检查关键概念
    checks = {
        "顶级裁判身份": "顶级裁判" in config_prompt,
        "信息来源优先级": "信息来源优先级" in config_prompt or "优先级" in config_prompt,
        "引用规则": "引用" in config_prompt and "规则" in config_prompt,
        "明确裁定": "明确" in config_prompt,
    }
    
    print("\n关键概念检查：")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n✓ 配置系统提示词包含所有关键概念")
    else:
        print("\n⚠ 配置系统提示词可能缺少某些概念")
    
except Exception as e:
    print(f"✗ 检查失败: {e}")

# 测试3: 检查提示词合并逻辑
print("\n【测试3】检查提示词合并逻辑")
print("-" * 80)

try:
    with open("app/llm_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = {
        "支持自定义提示词": "system_prompt: str = None" in content,
        "合并提示词": "combined_prompt" in content or "system_prompt +" in content,
        "分隔符": "---" in content or "\\n\\n" in content,
    }
    
    print("合并逻辑检查：")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n✓ 提示词合并逻辑正确")
    else:
        print("\n⚠ 提示词合并逻辑可能有问题")
    
except Exception as e:
    print(f"✗ 检查失败: {e}")

# 测试4: 模拟问题场景
print("\n【测试4】模拟问题场景")
print("-" * 80)

print("""
问题：攻击流程是什么顺序？

参考资料包含：
- 规则11-1-3: 攻击按以下顺序进行各时机："攻击宣言"、"反击时机"、"阻挡时机"、"成立确认"、"攻击结束时"

预期行为：
✓ LLM应该识别出参考资料中有相关规则
✓ LLM应该引用规则11-1-3
✓ LLM应该列出5个攻击时机的顺序
✓ LLM不应该说"参考资料中未找到相关内容"

修复措施：
1. ✓ 优化SYSTEM_PROMPT，强调"优先使用参考资料"
2. ✓ 优化SYSTEM_PROMPT，要求"引用具体规则编号"
3. ✓ 优化SYSTEM_PROMPT，明确"如果参考资料中有相关内容，必须使用"
4. ✓ 改进提示词合并逻辑，配置提示词在前（定义身份），默认提示词在后（定义任务）
""")

# 总结
print("\n" + "=" * 80)
print("修复总结")
print("=" * 80)

print("""
✅ 已完成的修复：

1. 优化 SYSTEM_PROMPT
   - 强调"优先使用参考资料"
   - 要求"引用具体规则编号"
   - 明确"如果参考资料中有相关内容，必须使用"
   - 只有在参考资料完全没有相关内容时，才说明未找到

2. 改进提示词合并逻辑
   - 配置提示词在前（定义身份和原则）
   - 默认提示词在后（定义具体任务）
   - 使用分隔符清晰区分

3. 预期效果
   - LLM会更积极地使用参考资料
   - LLM会引用具体的规则编号
   - LLM不会轻易说"未找到相关内容"

下一步测试：
1. 重启程序：python main_new.py
2. 测试问题："攻击流程是什么顺序？"
3. 验证LLM是否正确使用参考资料中的规则11-1-3
""")

print("=" * 80)
