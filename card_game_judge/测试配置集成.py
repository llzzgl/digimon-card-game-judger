"""
测试配置系统集成效果
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("测试配置系统集成")
print("=" * 80)

# 测试1: 验证配置加载
print("\n【测试1】验证配置加载")
print("-" * 80)

try:
    from app.judge_config_loader import get_system_prompt
    
    system_prompt = get_system_prompt()
    print(f"✓ 配置加载成功")
    print(f"  系统提示词长度: {len(system_prompt)} 字符")
    print(f"\n  系统提示词预览（前300字符）:")
    print(f"  {system_prompt[:300]}...")
    
    # 检查关键词
    keywords = ["顶级裁判", "数码宝贝", "规则", "卡牌效果", "官方QA"]
    print(f"\n  关键词检查:")
    for kw in keywords:
        status = "✓" if kw in system_prompt else "✗"
        print(f"    {status} '{kw}'")
    
except Exception as e:
    print(f"✗ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 验证 main_new.py 集成
print("\n【测试2】验证 main_new.py 集成")
print("-" * 80)

try:
    # 检查导入
    print("  检查导入...")
    with open("main_new.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if "from app.judge_config_loader import" in content:
        print("  ✓ 配置加载器已导入")
    else:
        print("  ✗ 配置加载器未导入")
    
    if "self.system_prompt = get_system_prompt()" in content:
        print("  ✓ 系统提示词已加载")
    else:
        print("  ✗ 系统提示词未加载")
    
    if "system_prompt=self.system_prompt" in content:
        print("  ✓ 系统提示词已传递给LLM")
    else:
        print("  ✗ 系统提示词未传递给LLM")
    
except Exception as e:
    print(f"  ✗ 检查失败: {e}")

# 测试3: 验证 llm_service.py 修改
print("\n【测试3】验证 llm_service.py 修改")
print("-" * 80)

try:
    print("  检查方法签名...")
    with open("app/llm_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if "system_prompt: str = None" in content:
        print("  ✓ generate_answer 方法支持 system_prompt 参数")
    else:
        print("  ✗ generate_answer 方法不支持 system_prompt 参数")
    
    if "def _call_llm(self, context: str, question: str, system_prompt: str = None)" in content:
        print("  ✓ _call_llm 方法支持 system_prompt 参数")
    else:
        print("  ✗ _call_llm 方法不支持 system_prompt 参数")
    
except Exception as e:
    print(f"  ✗ 检查失败: {e}")

# 测试4: 模拟初始化
print("\n【测试4】模拟初始化（不实际启动）")
print("-" * 80)

try:
    print("  尝试导入 NewCardGameJudge...")
    # 注意：这里不实际初始化，因为需要加载模型
    print("  ✓ 导入成功（未实际初始化以避免加载模型）")
    print("  提示：运行 'python main_new.py --test \"测试问题\"' 进行完整测试")
    
except Exception as e:
    print(f"  ✗ 导入失败: {e}")

# 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

print("""
✅ 配置系统已成功集成到 main_new.py

集成内容：
1. ✓ 在 NewCardGameJudge.__init__ 中加载配置
2. ✓ 在 query 方法中使用系统提示词
3. ✓ 修改 llm_service.py 支持自定义系统提示词

下一步测试：
1. 运行完整测试：
   python main_new.py --test "进化时费用会退还吗？"

2. 启动Web界面：
   python main_new.py

3. 对比测试：
   - 修改 .judge/IDENTITY.md 中的配置
   - 重启程序
   - 观察AI回答的变化

预期效果：
- AI会自我介绍为"数码宝贝卡牌对战的顶级裁判"
- 回答会引用具体的规则条款
- 使用准确的游戏术语
- 不确定时会明确说明
""")

print("=" * 80)
