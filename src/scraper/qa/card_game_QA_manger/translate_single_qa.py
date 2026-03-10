"""
翻译单条QA（用于调试）
"""
import json
from pathlib import Path
from translate_qa_with_terminology import MultiLLMQATranslator


def translate_single():
    """翻译单条QA进行测试"""
    print("="*60)
    print("单条QA翻译测试")
    print("="*60)
    
    # 加载日文QA
    input_file = Path(__file__).parent / "official_qa_jp.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        qa_list = json.load(f)
    
    print(f"\n总共 {len(qa_list)} 条QA")
    
    # 选择要翻译的QA
    qa_index = input("\n请输入要翻译的QA索引 (0-{}, 默认0): ".format(len(qa_list)-1)).strip()
    qa_index = int(qa_index) if qa_index else 0
    
    if qa_index < 0 or qa_index >= len(qa_list):
        print("无效索引")
        return
    
    qa_item = qa_list[qa_index]
    
    print("\n" + "="*60)
    print("原始QA")
    print("="*60)
    print(f"QA编号: {qa_item.get('qa_number', 'N/A')}")
    print(f"卡号: {qa_item.get('card_no', 'N/A')}")
    print(f"\n问题:\n{qa_item.get('question', '')}")
    print(f"\n答案:\n{qa_item.get('answer', '')}")
    
    # 创建翻译器
    print("\n" + "="*60)
    print("初始化翻译器")
    print("="*60)
    
    try:
        translator = MultiLLMQATranslator(llm_type="qwen")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 显示提示词信息
    print("\n" + "="*60)
    print("提示词信息")
    print("="*60)
    print(f"提示词长度: {len(translator.translation_prompt)} 字符")
    print(f"术语数量: {len(translator.terminology)}")
    print(f"卡牌数量: {len(translator.card_mapping)}")
    
    # 翻译
    print("\n" + "="*60)
    print("开始翻译")
    print("="*60)
    
    try:
        translated = translator.translate_qa_item(qa_item)
        
        print("\n" + "="*60)
        print("翻译结果")
        print("="*60)
        print(f"\n问题:\n{translated.get('question', '')}")
        print(f"\n答案:\n{translated.get('answer', '')}")
        
        # 保存结果
        output_file = Path(__file__).parent / "single_qa_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([translated], f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n✗ 翻译失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    translate_single()
