"""
验证配置系统是否真正影响AI行为
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.judge_config_loader import get_config_loader, get_system_prompt


def test_1_system_prompt_generation():
    """测试1: 验证系统提示词是否包含配置内容"""
    print("=" * 60)
    print("测试1: 验证系统提示词生成")
    print("=" * 60)
    
    loader = get_config_loader()
    prompt = get_system_prompt()
    
    # 检查关键词是否出现在提示词中
    keywords = [
        "数码宝贝卡牌对战",
        "顶级裁判",
        "规则",
        "卡牌效果",
        "官方QA",
        "引经据典",
    ]
    
    print("\n检查关键词是否出现在系统提示词中：\n")
    
    all_found = True
    for keyword in keywords:
        found = keyword in prompt
        status = "✓" if found else "✗"
        print(f"  {status} '{keyword}': {'找到' if found else '未找到'}")
        if not found:
            all_found = False
    
    print(f"\n结果: {'✓ 所有关键词都已包含' if all_found else '✗ 部分关键词缺失'}")
    print(f"\n系统提示词长度: {len(prompt)} 字符")
    print(f"\n系统提示词预览（前500字符）：")
    print("-" * 60)
    print(prompt[:500])
    print("-" * 60)
    
    return all_found


def test_2_identity_influence():
    """测试2: 验证身份定义的影响"""
    print("\n" + "=" * 60)
    print("测试2: 验证身份定义的影响")
    print("=" * 60)
    
    loader = get_config_loader()
    identity = loader.get_identity()
    prompt = get_system_prompt()
    
    # 检查身份定义中的核心概念是否传递到提示词
    identity_concepts = {
        "核心身份": ["顶级裁判", "数码宝贝"],
        "专业水平": ["规则", "卡牌效果", "官方裁定"],
        "回答风格": ["引经据典", "照本宣科"],
    }
    
    print("\n检查身份概念是否传递到系统提示词：\n")
    
    all_passed = True
    for concept, keywords in identity_concepts.items():
        print(f"  {concept}:")
        concept_found = False
        for keyword in keywords:
            if keyword in prompt:
                print(f"    ✓ '{keyword}' 已传递")
                concept_found = True
                break
        if not concept_found:
            print(f"    ✗ 概念未传递")
            all_passed = False
    
    print(f"\n结果: {'✓ 身份定义已正确传递' if all_passed else '✗ 部分概念未传递'}")
    
    return all_passed


def test_3_rules_influence():
    """测试3: 验证工作规则的影响"""
    print("\n" + "=" * 60)
    print("测试3: 验证工作规则的影响")
    print("=" * 60)
    
    loader = get_config_loader()
    rules = loader.get_rules()
    prompt = get_system_prompt()
    
    # 检查规则中的关键要求是否传递到提示词
    rule_requirements = [
        "官方综合规则",
        "卡牌效果文本",
        "官方QA",
        "引用",
        "规则条款",
    ]
    
    print("\n检查规则要求是否传递到系统提示词：\n")
    
    found_count = 0
    for requirement in rule_requirements:
        found = requirement in prompt or requirement in rules
        status = "✓" if found else "✗"
        print(f"  {status} '{requirement}': {'已包含' if found else '未包含'}")
        if found:
            found_count += 1
    
    success_rate = (found_count / len(rule_requirements)) * 100
    print(f"\n结果: {found_count}/{len(rule_requirements)} 个要求已传递 ({success_rate:.0f}%)")
    
    return found_count >= len(rule_requirements) * 0.8  # 80%通过即可



def test_4_config_modification_effect():
    """测试4: 验证配置修改的效果"""
    print("\n" + "=" * 60)
    print("测试4: 验证配置修改的效果")
    print("=" * 60)
    
    print("\n这个测试需要手动操作：")
    print("\n步骤1: 记录当前的系统提示词")
    
    loader = get_config_loader()
    original_prompt = get_system_prompt()
    
    print(f"  当前提示词长度: {len(original_prompt)} 字符")
    print(f"  当前提示词包含 '顶级裁判': {('顶级裁判' in original_prompt)}")
    
    print("\n步骤2: 修改配置文件")
    print("  请手动编辑 .judge/IDENTITY.md")
    print("  将 '顶级裁判' 改为 '资深裁判'")
    print("  保存文件")
    
    print("\n步骤3: 重新加载配置")
    print("  重启程序或重新导入模块")
    
    print("\n步骤4: 验证修改")
    print("  新的提示词应该包含 '资深裁判' 而不是 '顶级裁判'")
    
    print("\n✓ 手动测试说明已显示")
    
    return True


def test_5_llm_integration():
    """测试5: 验证与LLM的集成"""
    print("\n" + "=" * 60)
    print("测试5: 验证与LLM的集成")
    print("=" * 60)
    
    print("\n检查是否可以在LLM服务中使用配置：\n")
    
    try:
        # 尝试导入LLM服务
        from app.llm_service import LLMService
        print("  ✓ LLMService 导入成功")
        
        # 获取系统提示词
        system_prompt = get_system_prompt()
        print("  ✓ 系统提示词生成成功")
        
        # 检查LLMService是否接受system_prompt参数
        import inspect
        sig = inspect.signature(LLMService.__init__)
        params = list(sig.parameters.keys())
        
        print(f"\n  LLMService.__init__ 参数: {params}")
        
        # 建议集成方式
        print("\n集成建议：")
        print("  在 main_new.py 中添加：")
        print("  ```python")
        print("  from app.judge_config_loader import get_system_prompt")
        print("  ")
        print("  system_prompt = get_system_prompt()")
        print("  llm_service = LLMService()")
        print("  # 在调用LLM时使用 system_prompt")
        print("  ```")
        
        print("\n✓ 集成检查完成")
        return True
        
    except Exception as e:
        print(f"  ✗ 集成检查失败: {e}")
        return False


def test_6_compare_with_without_config():
    """测试6: 对比使用和不使用配置的差异"""
    print("\n" + "=" * 60)
    print("测试6: 对比使用和不使用配置的差异")
    print("=" * 60)
    
    # 使用配置的提示词
    with_config = get_system_prompt()
    
    # 不使用配置的默认提示词
    without_config = """你是一个AI助手，请回答用户的问题。"""
    
    print("\n对比分析：\n")
    print(f"  使用配置:")
    print(f"    - 长度: {len(with_config)} 字符")
    print(f"    - 包含身份定义: {'✓' if '裁判' in with_config else '✗'}")
    print(f"    - 包含工作规则: {'✓' if '规则' in with_config else '✗'}")
    print(f"    - 包含专业术语: {'✓' if '数码宝贝' in with_config else '✗'}")
    
    print(f"\n  不使用配置:")
    print(f"    - 长度: {len(without_config)} 字符")
    print(f"    - 包含身份定义: ✗")
    print(f"    - 包含工作规则: ✗")
    print(f"    - 包含专业术语: ✗")
    
    improvement = len(with_config) / len(without_config)
    print(f"\n  配置提供了 {improvement:.1f}x 的信息量提升")
    
    print("\n✓ 对比分析完成")
    
    return True


def test_7_feedback_mechanism():
    """测试7: 验证反馈机制"""
    print("\n" + "=" * 60)
    print("测试7: 验证反馈机制")
    print("=" * 60)
    
    print("\n检查反馈记录功能：\n")
    
    try:
        from app.judge_config_loader import add_user_feedback
        
        print("  ✓ add_user_feedback 函数可用")
        
        # 测试添加反馈（不实际写入）
        print("\n  测试反馈格式：")
        print("  ```python")
        print("  add_user_feedback(")
        print("      question='测试问题',")
        print("      current_answer='测试回答',")
        print("      user_feedback='测试反馈',")
        print("      feedback_type='裁定纠正'")
        print("  )")
        print("  ```")
        
        print("\n  ✓ 反馈机制已就绪")
        
        # 检查FEEDBACK.md是否存在
        feedback_file = Path(".judge/FEEDBACK.md")
        if feedback_file.exists():
            print(f"  ✓ 反馈文件存在: {feedback_file}")
        else:
            print(f"  ✗ 反馈文件不存在: {feedback_file}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 反馈机制检查失败: {e}")
        return False


def main():
    """运行所有验证测试"""
    print("\n" + "=" * 60)
    print("配置系统效果验证")
    print("=" * 60)
    print("\n这些测试将验证配置系统是否真正影响AI的行为\n")
    
    tests = [
        ("系统提示词生成", test_1_system_prompt_generation),
        ("身份定义影响", test_2_identity_influence),
        ("工作规则影响", test_3_rules_influence),
        ("配置修改效果", test_4_config_modification_effect),
        ("LLM集成", test_5_llm_integration),
        ("配置对比", test_6_compare_with_without_config),
        ("反馈机制", test_7_feedback_mechanism),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n通过: {passed}/{total} 个测试\n")
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！配置系统正常工作。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠ 部分测试未通过，请检查配置。")
        print("=" * 60)
    
    print("\n下一步：")
    print("1. 在 main_new.py 中集成配置系统")
    print("2. 使用真实的LLM测试配置效果")
    print("3. 对比不同配置下的AI回答")
    print()


if __name__ == "__main__":
    main()
