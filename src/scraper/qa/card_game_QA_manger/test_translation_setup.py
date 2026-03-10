"""
测试翻译工具的配置和数据加载
"""
from pathlib import Path
import json

def test_paths():
    """测试所有路径是否存在"""
    print("="*60)
    print("测试路径配置")
    print("="*60)
    
    base_dir = Path(__file__).parent.parent.parent
    
    # 测试术语表路径
    terminology_path = base_dir / "digimon_card_data" / "term_mapping" / "game_mechanics_keywords.json"
    print(f"\n1. 术语表路径:")
    print(f"   {terminology_path}")
    print(f"   存在: {terminology_path.exists()}")
    
    if terminology_path.exists():
        with open(terminology_path, 'r', encoding='utf-8') as f:
            terms = json.load(f)
        print(f"   术语数量: {len(terms)}")
        # 显示前5个术语
        print(f"   示例术语:")
        for i, (jp, cn) in enumerate(list(terms.items())[:5]):
            cn_str = cn[0] if isinstance(cn, list) else cn
            print(f"     {jp} → {cn_str}")
    
    # 测试卡牌数据路径
    card_data_path = base_dir / "digimon_card_data" / "digimon_card_data_chiness" / "digimon_cards_cn.json"
    print(f"\n2. 卡牌数据路径:")
    print(f"   {card_data_path}")
    print(f"   存在: {card_data_path.exists()}")
    
    if card_data_path.exists():
        with open(card_data_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        print(f"   卡牌数量: {len(cards)}")
        # 显示第一张卡
        if cards:
            card = cards[0]
            print(f"   示例卡牌:")
            print(f"     卡号: {card.get('card_no', 'N/A')}")
            print(f"     中文名: {card.get('name_cn', 'N/A')}")
            print(f"     日文名: {card.get('name_jp', 'N/A')}")
    
    # 测试日文QA路径
    input_qa_path = Path(__file__).parent / "official_qa_jp.json"
    print(f"\n3. 日文QA路径:")
    print(f"   {input_qa_path}")
    print(f"   存在: {input_qa_path.exists()}")
    
    if input_qa_path.exists():
        with open(input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        print(f"   QA数量: {len(qa_list)}")
        # 显示第一条QA
        if qa_list:
            qa = qa_list[0]
            print(f"   示例QA:")
            print(f"     编号: {qa.get('qa_number', 'N/A')}")
            print(f"     卡号: {qa.get('card_no', 'N/A')}")
            print(f"     问题: {qa.get('question', 'N/A')[:50]}...")
    
    # 测试.env文件
    env_path = base_dir / "card_game_judge" / ".env"
    print(f"\n4. 环境变量文件:")
    print(f"   {env_path}")
    print(f"   存在: {env_path.exists()}")
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   配置项数量: {len([l for l in lines if '=' in l and not l.strip().startswith('#')])}")
        # 检查关键API密钥
        api_keys = ['DASHSCOPE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY']
        for key in api_keys:
            found = any(key in line for line in lines)
            print(f"   {key}: {'✓' if found else '✗'}")
    
    print("\n" + "="*60)
    print("路径测试完成")
    print("="*60)


def test_import():
    """测试导入翻译模块"""
    print("\n测试导入翻译模块...")
    try:
        from translate_qa_with_terminology import MultiLLMQATranslator
        print("✓ 模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_paths()
    test_import()
