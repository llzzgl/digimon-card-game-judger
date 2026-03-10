"""
词汇对照表使用示例
演示如何在实际项目中使用生成的词汇对照表
"""

from query_terms import TermQuery
from pathlib import Path


def example_1_basic_query():
    """示例1: 基本查询"""
    print("\n" + "=" * 60)
    print("示例1: 基本查询")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    # 查询数码兽名称
    digimon_names = ["亚古兽", "加布兽", "巴达兽", "比丘兽"]
    print("\n数码兽名称对照:")
    for name in digimon_names:
        jp_names = query.query_cn_to_jp(name)
        if jp_names:
            print(f"  {name} -> {', '.join(jp_names)}")
    
    # 查询卡牌属性
    print("\n卡牌属性对照:")
    attributes = ["疫苗", "数据", "病毒"]
    for attr in attributes:
        jp_attrs = query.query_cn_to_jp(attr)
        if jp_attrs:
            print(f"  {attr} -> {', '.join(jp_attrs)}")


def example_2_translate_card_info():
    """示例2: 翻译卡牌信息"""
    print("\n" + "=" * 60)
    print("示例2: 翻译卡牌信息")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    # 模拟一张中文卡牌的信息
    card_info = {
        "name": "战斗暴龙兽",
        "type": "数码兽卡",
        "color": "红",
        "level": "究极体",
        "attribute": "疫苗",
        "rarity": "SR"
    }
    
    print("\n原始中文卡牌信息:")
    for key, value in card_info.items():
        print(f"  {key}: {value}")
    
    print("\n对应的日文词汇:")
    for key, value in card_info.items():
        jp_terms = query.query_cn_to_jp(value)
        if jp_terms:
            print(f"  {key}: {value} -> {', '.join(jp_terms)}")
        else:
            print(f"  {key}: {value} -> (未找到对照)")


def example_3_search_by_category():
    """示例3: 按类别搜索"""
    print("\n" + "=" * 60)
    print("示例3: 按类别搜索")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    categories = ["颜色", "形态", "属性"]
    
    for category in categories:
        print(f"\n{category}类别:")
        terms = query.get_category_terms(category)
        if terms:
            for cn_term, jp_terms in sorted(terms.items()):
                print(f"  {cn_term} -> {', '.join(jp_terms)}")


def example_4_fuzzy_search():
    """示例4: 模糊搜索"""
    print("\n" + "=" * 60)
    print("示例4: 模糊搜索")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    # 搜索包含"龙"的数码兽
    print("\n搜索包含'龙'的数码兽 (前10个):")
    results = query.search_cn("龙")
    for i, (cn_term, jp_terms) in enumerate(sorted(results.items())[:10], 1):
        print(f"  {i}. {cn_term} -> {', '.join(jp_terms)}")
    
    # 搜索包含"モン"的日文词汇
    print("\n搜索包含'モン'的日文词汇 (前10个):")
    results = query.search_jp("モン")
    for i, (jp_term, cn_terms) in enumerate(sorted(results.items())[:10], 1):
        print(f"  {i}. {jp_term} -> {', '.join(cn_terms)}")


def example_5_batch_translation():
    """示例5: 批量翻译"""
    print("\n" + "=" * 60)
    print("示例5: 批量翻译")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    # 批量翻译一组中文词汇
    cn_terms = [
        "红", "蓝", "黄", "绿", "黑", "紫",
        "幼年期", "成长期", "成熟期", "完全体", "究极体",
        "疫苗", "数据", "病毒"
    ]
    
    print("\n批量翻译结果:")
    translation_table = {}
    for cn_term in cn_terms:
        jp_terms = query.query_cn_to_jp(cn_term)
        if jp_terms:
            translation_table[cn_term] = jp_terms[0]  # 取第一个日文词
            print(f"  {cn_term} -> {jp_terms[0]}")
    
    # 保存翻译表
    import json
    output_file = Path(__file__).parent / "translation_table_example.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translation_table, f, ensure_ascii=False, indent=2)
    
    print(f"\n翻译表已保存到: {output_file}")


def example_6_reverse_lookup():
    """示例6: 反向查询（日文到中文）"""
    print("\n" + "=" * 60)
    print("示例6: 反向查询（日文到中文）")
    print("=" * 60)
    
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    query = TermQuery(mapping_file)
    
    # 查询日文词汇对应的中文
    jp_terms = ["アグモン", "ガブモン", "パタモン", "テイルモン"]
    
    print("\n日文到中文查询:")
    for jp_term in jp_terms:
        cn_terms = query.query_jp_to_cn(jp_term)
        if cn_terms:
            print(f"  {jp_term} -> {', '.join(cn_terms)}")
        else:
            print(f"  {jp_term} -> (未找到对照)")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("数码宝贝卡牌中日文词汇对照表使用示例")
    print("=" * 60)
    
    # 检查词汇对照表文件是否存在
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    if not mapping_file.exists():
        print("\n错误: 词汇对照表文件不存在")
        print("请先运行 extract_terms.py 生成词汇对照表")
        return
    
    # 运行所有示例
    example_1_basic_query()
    example_2_translate_card_info()
    example_3_search_by_category()
    example_4_fuzzy_search()
    example_5_batch_translation()
    example_6_reverse_lookup()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
