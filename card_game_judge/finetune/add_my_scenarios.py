# -*- coding: utf-8 -*-
"""
添加你自己的场面分析案例
复制这个文件，填入你的实际案例
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DTCGDataCollector


def add_my_scenarios(collector: DTCGDataCollector):
    """
    在这里添加你自己的场面分析案例
    
    使用方法：
    1. 复制下面的模板
    2. 填入你的实际游戏场面
    3. 提供详细的分析过程
    4. 运行脚本生成训练数据
    """
    
    scenario_instruction = """你是数码宝贝卡牌游戏(DTCG)的规则专家和裁判。
请分析给定的游戏场面，综合考虑：
1. 涉及的卡牌效果
2. 相关的规则条款
3. 效果的触发时机和处理顺序
4. 最终的场面结果

给出详细的分析过程和结论。"""
    
    # ========== 在这里添加你的案例 ==========
    
    # 案例模板1：你的实际游戏场面
    my_scenario_1 = {
        "question": """
        [在这里描述你的游戏场面]
        
        例如：
        我方联展了bt23-032土偶兽，把对方的数码兽退化成bt24-016拉米亚兽，
        并选择其主要阶段开始时攻击。土偶进化源中有bt23-027天使兽和
        bt23-050甲龙兽。对方拉米亚进化源中有bt21-001基基兽。
        此时移交回合后会发生什么？
        """.strip(),
        
        "answer": """
        [在这里写详细的分析]
        
        建议包含以下部分：
        
        【涉及的卡牌效果】
        1. BT23-032 土偶兽：[效果描述]
        2. BT24-016 拉米亚兽：[效果描述]
        ...
        
        【相关规则】
        • 规则 X-X：[规则内容]
        • 规则 Y-Y：[规则内容]
        
        【效果时机分析】
        [分析各效果何时触发]
        
        【处理顺序】
        1. [第一步]
        2. [第二步]
        ...
        
        【场面推导】
        [逐步推导场面变化]
        
        【结论】
        [明确的结论]
        
        【注意事项】
        [如有需要，补充注意事项]
        """.strip(),
        
        "tags": ["场面分析", "联展", "退化", "效果触发"]  # 添加相关标签
    }
    
    # 如果你暂时没有案例，可以注释掉下面这行
    # collector.add_custom_qa(
    #     question=my_scenario_1["question"],
    #     answer=my_scenario_1["answer"],
    #     instruction=scenario_instruction,
    #     tags=my_scenario_1["tags"]
    # )
    
    # 案例模板2：继续添加更多案例
    # my_scenario_2 = {
    #     "question": """...""",
    #     "answer": """...""",
    #     "tags": [...]
    # }
    # collector.add_custom_qa(...)
    
    # 案例模板3
    # my_scenario_3 = {
    #     "question": """...""",
    #     "answer": """...""",
    #     "tags": [...]
    # }
    # collector.add_custom_qa(...)
    
    # ========== 添加更多案例 ==========
    
    print(f"✅ 添加了你的场面分析案例")


def main():
    """主函数"""
    print("=" * 60)
    print("添加我的场面分析案例")
    print("=" * 60)
    
    # 初始化收集器
    collector = DTCGDataCollector(output_dir="training_data")
    
    # 添加你的案例
    add_my_scenarios(collector)
    
    # 显示统计
    collector.print_statistics()
    
    # 导出数据
    if collector.get_statistics()['total_count'] > 0:
        collector.export_jsonl("my_scenarios.jsonl")
        collector.export_json("my_scenarios.json")
        
        print("\n" + "=" * 60)
        print("✅ 你的场面分析数据已生成")
        print("=" * 60)
        print("\n📝 下一步：")
        print("1. 合并到主训练数据：")
        print("   type training_data\\my_scenarios.jsonl >> training_data\\dtcg_finetune_data.jsonl")
        print("2. 重新训练模型：")
        print("   python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl")
    else:
        print("\n⚠️ 没有添加任何案例")
        print("   请编辑 add_my_scenarios.py，取消注释并填入你的案例")


if __name__ == "__main__":
    main()
