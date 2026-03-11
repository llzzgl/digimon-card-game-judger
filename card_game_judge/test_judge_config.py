"""
测试裁判配置系统
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.judge_config_loader import (
    JudgeConfigLoader,
    get_config_loader,
    get_system_prompt,
    add_user_feedback
)


def test_load_configs():
    """测试加载配置文件"""
    print("=== 测试1: 加载配置文件 ===\n")
    
    loader = JudgeConfigLoader()
    configs = loader.load_all()
    
    print(f"✓ 已加载 {len(configs)} 个配置文件")
    for key in configs.keys():
        length = len(configs[key])
        print(f"  - {key}: {length} 字符")
    print()


def test_get_identity():
    """测试获取身份定义"""
    print("=== 测试2: 获取身份定义 ===\n")
    
    loader = get_config_loader()
    identity = loader.get_identity()
    
    print("身份定义（前300字符）:")
    print(identity[:300])
    print("...\n")


def test_get_rules():
    """测试获取工作规则"""
    print("=== 测试3: 获取工作规则 ===\n")
    
    loader = get_config_loader()
    rules = loader.get_rules()
    
    print("工作规则（前300字符）:")
    print(rules[:300])
    print("...\n")


def test_system_prompt():
    """测试生成系统提示词"""
    print("=== 测试4: 生成系统提示词 ===\n")
    
    prompt = get_system_prompt()
    
    print("系统提示词（前500字符）:")
    print(prompt[:500])
    print("...\n")


def test_add_feedback():
    """测试添加用户反馈"""
    print("=== 测试5: 添加用户反馈 ===\n")
    
    success = add_user_feedback(
        question="测试问题：进化时费用会退还吗？",
        current_answer="费用会退还到记忆区",
        user_feedback="这是错误的，费用不会退还",
        feedback_type="裁定纠正",
        improvement="已更新记忆系统",
        status="已改进"
    )
    
    if success:
        print("✓ 成功添加用户反馈")
    else:
        print("✗ 添加用户反馈失败")
    print()


def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("裁判配置系统测试")
    print("="*50 + "\n")
    
    try:
        test_load_configs()
        test_get_identity()
        test_get_rules()
        test_system_prompt()
        # test_add_feedback()  # 注释掉，避免实际修改文件
        
        print("="*50)
        print("✓ 所有测试通过")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
