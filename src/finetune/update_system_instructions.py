# -*- coding: utf-8 -*-
"""
更新训练数据的系统指令
使其与改进后的推理模式保持一致
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DTCGDataCollector


# 改进的系统指令
IMPROVED_SYSTEM_INSTRUCTIONS = {
    "rule": """你是数码宝贝卡牌游戏(DTCG)的规则专家。
请根据官方综合规则准确回答问题。
如果涉及复杂规则，请：
1. 引用具体规则条款
2. 解释规则含义
3. 举例说明应用""",

    "keyword": """你是数码宝贝卡牌游戏(DTCG)的规则专家。
请解释关键词效果的含义和使用方法。
包括：
1. 关键词的定义
2. 触发条件
3. 处理方式
4. 常见应用场景""",

    "timing": """你是数码宝贝卡牌游戏(DTCG)的规则专家。
请解释效果时机的触发条件和处理方式。
包括：
1. 何时触发
2. 如何处理
3. 与其他效果的交互""",

    "qa": """你是数码宝贝卡牌游戏(DTCG)的官方裁定专家。
请根据官方Q&A回答问题。
提供：
1. 明确的裁定结论
2. 相关规则依据
3. 注意事项""",

    "scenario": """你是数码宝贝卡牌游戏(DTCG)的规则专家和裁判。
请分析游戏场面，综合考虑：
1. 涉及的卡牌效果
2. 相关的规则条款
3. 效果的触发时机和处理顺序
4. 最终的场面结果

按以下结构回答：
【涉及的卡牌效果】
【相关规则】
【处理顺序】
【结论】""",

    "general": """你是数码宝贝卡牌游戏(DTCG)的规则专家。
请准确回答关于游戏规则的问题。
如果问题复杂，请：
1. 分析问题涉及的规则
2. 逐步推导结论
3. 给出明确答案""",

    "card": """你是数码宝贝卡牌游戏(DTCG)的卡牌数据专家。
请准确回答关于卡牌信息和效果的问题。
提供：
1. 卡牌基本信息
2. 效果详细说明
3. 使用建议（如适用）"""
}


def update_data_collector_instructions():
    """更新 data_collector.py 中的系统指令"""
    
    collector_path = Path(__file__).parent / "data_collector.py"
    
    print("=" * 60)
    print("更新训练数据系统指令")
    print("=" * 60)
    print(f"\n文件: {collector_path}")
    
    # 读取文件
    with open(collector_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换 SYSTEM_INSTRUCTIONS
    old_instructions_start = content.find('SYSTEM_INSTRUCTIONS = {')
    if old_instructions_start == -1:
        print("❌ 未找到 SYSTEM_INSTRUCTIONS 定义")
        return False
    
    # 找到结束位置
    old_instructions_end = content.find('}', old_instructions_start)
    # 找到完整的字典结束（可能有多层嵌套）
    brace_count = 1
    pos = old_instructions_start + len('SYSTEM_INSTRUCTIONS = {')
    while brace_count > 0 and pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
        pos += 1
    old_instructions_end = pos
    
    # 构建新的指令字典字符串
    new_instructions = "SYSTEM_INSTRUCTIONS = {\n"
    for key, value in IMPROVED_SYSTEM_INSTRUCTIONS.items():
        # 转义引号和换行
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        new_instructions += f'        "{key}": """{value}""",\n'
    new_instructions += "    }"
    
    # 替换
    new_content = (
        content[:old_instructions_start] +
        new_instructions +
        content[old_instructions_end:]
    )
    
    # 写回文件
    with open(collector_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 系统指令已更新")
    print("\n更新的指令类型:")
    for key in IMPROVED_SYSTEM_INSTRUCTIONS.keys():
        print(f"  • {key}")
    
    return True


def regenerate_all_data():
    """重新生成所有训练数据"""
    print("\n" + "=" * 60)
    print("重新生成训练数据")
    print("=" * 60)
    
    import subprocess
    
    # 运行 collect_all_data.py
    result = subprocess.run(
        [sys.executable, "collect_all_data.py"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 训练数据重新生成完成")
        print(result.stdout)
    else:
        print("❌ 训练数据生成失败")
        print(result.stderr)
        return False
    
    # 重新生成场面分析数据
    result = subprocess.run(
        [sys.executable, "add_scenario_analysis_data.py"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 场面分析数据重新生成完成")
        print(result.stdout)
    else:
        print("❌ 场面分析数据生成失败")
        print(result.stderr)
        return False
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新训练数据系统指令")
    parser.add_argument("--update-only", action="store_true",
                        help="仅更新指令定义，不重新生成数据")
    parser.add_argument("--regenerate", action="store_true",
                        help="更新指令并重新生成所有数据")
    
    args = parser.parse_args()
    
    # 更新指令定义
    success = update_data_collector_instructions()
    
    if not success:
        return
    
    # 是否重新生成数据
    if args.regenerate:
        regenerate_all_data()
    elif not args.update_only:
        print("\n" + "=" * 60)
        print("下一步")
        print("=" * 60)
        print("\n选项1: 重新生成所有训练数据（推荐）")
        print("  python update_system_instructions.py --regenerate")
        print("\n选项2: 仅更新新增的场面分析数据")
        print("  python add_scenario_analysis_data.py")
        print("\n选项3: 手动更新现有数据")
        print("  编辑 training_data/*.jsonl 文件")


if __name__ == "__main__":
    main()
