"""
对比测试：使用配置 vs 不使用配置的AI回答差异
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.judge_config_loader import get_system_prompt


def get_default_prompt():
    """获取默认的系统提示词（不使用配置）"""
    return """你是一个AI助手，请回答用户关于数码宝贝卡牌游戏的问题。"""


def get_configured_prompt():
    """获取配置的系统提示词"""
    return get_system_prompt()


def compare_prompts():
    """对比两种提示词"""
    print("=" * 80)
    print("对比测试：配置系统的效果")
    print("=" * 80)
    
    default = get_default_prompt()
    configured = get_configured_prompt()
    
    print("\n【方案A：不使用配置】")
    print("-" * 80)
    print(default)
    print("-" * 80)
    print(f"长度: {len(default)} 字符")
    
    print("\n【方案B：使用配置系统】")
    print("-" * 80)
    print(configured[:500] + "..." if len(configured) > 500 else configured)
    print("-" * 80)
    print(f"长度: {len(configured)} 字符")
    
    print("\n【差异分析】")
    print("-" * 80)
    
    # 分析包含的关键概念
    concepts = {
        "身份定义": ["裁判", "顶级", "专业"],
        "工作规则": ["规则", "优先级", "流程"],
        "专业术语": ["数码宝贝", "卡牌", "效果"],
        "质量要求": ["准确", "引用", "依据"],
        "记忆系统": ["记忆", "验证", "学习"],
    }
    
    print("\n概念覆盖对比：\n")
    print(f"{'概念类别':<15} {'方案A':<10} {'方案B':<10}")
    print("-" * 40)
    
    for category, keywords in concepts.items():
        in_default = any(kw in default for kw in keywords)
        in_configured = any(kw in configured for kw in keywords)
        
        default_mark = "✓" if in_default else "✗"
        configured_mark = "✓" if in_configured else "✗"
        
        print(f"{category:<15} {default_mark:<10} {configured_mark:<10}")
    
    print("\n信息量对比：")
    print(f"  方案A: {len(default)} 字符")
    print(f"  方案B: {len(configured)} 字符")
    print(f"  提升: {len(configured) / len(default):.1f}x")
    
    print("\n" + "=" * 80)


def simulate_llm_behavior():
    """模拟LLM在不同配置下的行为差异"""
    print("\n模拟LLM行为差异")
    print("=" * 80)
    
    test_question = "进化时支付的费用会退还吗？"
    
    print(f"\n测试问题: {test_question}\n")
    
    print("【方案A：不使用配置】")
    print("-" * 80)
    print("预期行为:")
    print("  - 可能给出模糊的回答")
    print("  - 不会引用具体规则")
    print("  - 缺少专业术语")
    print("  - 不会说明信息来源")
    
    print("\n示例回答:")
    print("  '进化时的费用通常不会退还，但具体情况可能有所不同。'")
    
    print("\n【方案B：使用配置系统】")
    print("-" * 80)
    print("预期行为:")
    print("  - 给出明确的裁定")
    print("  - 引用综合规则条款")
    print("  - 使用专业术语")
    print("  - 说明信息来源")
    print("  - 提供详细解释")
    
    print("\n示例回答:")
    print("  '根据综合规则 8.1，进化时支付的费用不会退还。")
    print("  进化费用是从手牌支付到废弃区的，这个过程是单向的。")
    print("  即使进化的数码宝贝离场，已支付的费用也不会返回。'")
    
    print("\n" + "=" * 80)


def show_integration_example():
    """展示如何在代码中集成配置"""
    print("\n集成示例")
    print("=" * 80)
    
    print("\n在 main_new.py 中集成配置系统：\n")
    
    code_example = '''
# 在文件开头导入
from app.judge_config_loader import get_system_prompt

# 在初始化LLM服务时使用
def initialize_llm():
    """初始化LLM服务"""
    
    # 获取配置的系统提示词
    system_prompt = get_system_prompt()
    
    # 方式1: 如果LLM服务支持system参数
    llm_service = LLMService(system_prompt=system_prompt)
    
    # 方式2: 在每次调用时添加
    def query_with_config(user_question):
        full_prompt = f"""
{system_prompt}

用户问题: {user_question}

请根据你的身份和工作规则回答。
"""
        return llm_service.generate(full_prompt)
    
    return query_with_config

# 使用示例
query_func = initialize_llm()
answer = query_func("进化时费用会退还吗？")
'''
    
    print(code_example)
    
    print("\n" + "=" * 80)


def show_verification_steps():
    """展示验证步骤"""
    print("\n验证步骤")
    print("=" * 80)
    
    steps = [
        {
            "step": "1. 运行基础验证",
            "command": "python 验证配置效果.py",
            "expected": "所有测试通过，确认配置系统正常工作"
        },
        {
            "step": "2. 集成到主程序",
            "command": "修改 main_new.py，添加配置加载",
            "expected": "程序启动时加载配置，生成系统提示词"
        },
        {
            "step": "3. 测试实际效果",
            "command": "python main_new.py",
            "expected": "启动Web界面，测试AI回答"
        },
        {
            "step": "4. 对比测试",
            "command": "分别测试使用和不使用配置的回答",
            "expected": "使用配置的回答更专业、更准确"
        },
        {
            "step": "5. 修改配置测试",
            "command": "修改 .judge/IDENTITY.md，重启程序",
            "expected": "AI行为发生相应变化"
        },
    ]
    
    print("\n按以下步骤验证配置系统的效果：\n")
    
    for i, step_info in enumerate(steps, 1):
        print(f"{step_info['step']}")
        print(f"  操作: {step_info['command']}")
        print(f"  预期: {step_info['expected']}")
        print()
    
    print("=" * 80)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("配置系统效果对比测试")
    print("=" * 80)
    
    # 1. 对比提示词
    compare_prompts()
    
    # 2. 模拟行为差异
    simulate_llm_behavior()
    
    # 3. 展示集成示例
    show_integration_example()
    
    # 4. 展示验证步骤
    show_verification_steps()
    
    print("\n总结")
    print("=" * 80)
    print("""
配置系统通过以下方式影响AI行为：

1. 身份定义 → 确立专业角色和风格
2. 工作规则 → 规范裁定流程和标准
3. 系统提示词 → 传递给LLM的指令
4. 反馈机制 → 持续学习和改进

要验证效果，需要：
1. ✓ 运行 验证配置效果.py（已完成）
2. ⚠ 集成到 main_new.py（待完成）
3. ⚠ 使用真实LLM测试（待完成）
4. ⚠ 对比不同配置的效果（待完成）

下一步：在 main_new.py 中集成配置系统
""")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
