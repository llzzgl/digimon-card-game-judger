# -*- coding: utf-8 -*-
"""
查看提示词内容 - 不依赖导入
"""

print("=" * 80)
print("查看提示词内容")
print("=" * 80)

# 读取SYSTEM_PROMPT
print("\n[1] 读取 app/llm_service.py 中的 SYSTEM_PROMPT")
print("-" * 80)

with open("app/llm_service.py", "r", encoding="utf-8") as f:
    content = f.read()
    
    # 提取SYSTEM_PROMPT
    start = content.find('SYSTEM_PROMPT = """')
    if start != -1:
        start += len('SYSTEM_PROMPT = """')
        end = content.find('"""', start)
        system_prompt = content[start:end]
        
        print(system_prompt)
    else:
        print("未找到SYSTEM_PROMPT")

# 读取配置系统提示词
print("\n[2] 读取 .judge/IDENTITY.md 和 RULES.md")
print("-" * 80)

with open(".judge/IDENTITY.md", "r", encoding="utf-8") as f:
    identity = f.read()

with open(".judge/RULES.md", "r", encoding="utf-8") as f:
    rules = f.read()

print("IDENTITY.md (前500字符):")
print(identity[:500])
print("...")

print("\nRULES.md (前500字符):")
print(rules[:500])
print("...")

# 分析问题
print("\n[3] 问题分析")
print("-" * 80)

print("""
根据你的反馈，LLM仍然说"并未包含关于攻击流程的详细规则描述"。

可能的原因：
1. 参考资料格式不够清晰，LLM无法识别
2. 提示词过长，LLM注意力不集中
3. LLM模型本身的理解能力问题

建议的解决方案：
1. 简化参考资料格式，使用更清晰的标记
2. 在提示词中明确指出"参考资料第1条就是攻击流程规则"
3. 使用更强的提示词，例如：
   "注意：参考资料中的规则11-1-3明确列出了攻击流程的5个时机"
""")

print("\n[4] 建议的修改")
print("-" * 80)

new_system_prompt = """你是数码宝贝卡牌游戏（DTCG）裁判助手。

【关键提醒】
参考资料中如果包含规则编号（如"11-1-3"），这些就是官方规则，必须使用！

【重要原则】
1. 仔细阅读【参考资料】中的每一条内容
2. 如果看到规则编号（如"11-1-3"、"8.1"等），这就是官方规则
3. 必须基于这些规则给出明确的裁定
4. 引用具体的规则条款编号

【你的任务】
1. 逐条检查【参考资料】
2. 找出包含规则编号的内容
3. 基于这些规则回答问题
4. 引用规则编号

【参考资料】
{context}

【回答格式】
根据规则[编号]，[回答内容]...

【特别注意】
- 规则编号通常是数字加点号，如"11-1-3"、"8.1"
- 只要参考资料中有规则编号，就一定要使用
- 不要说"未找到"，除非真的完全没有相关内容
"""

print("建议的新SYSTEM_PROMPT:")
print(new_system_prompt)

print("\n" + "=" * 80)
