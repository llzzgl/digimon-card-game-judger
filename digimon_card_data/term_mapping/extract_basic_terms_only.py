"""
数码宝贝卡牌基础词汇提取工具
只提取卡牌的基础特征：名称、类型、颜色、形态、属性、稀有度
不提取种族中的括号内容，避免混乱
"""

import json
import re
from pathlib import Path
from collections import defaultdict


class BasicTermExtractor:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.cn_cards = {}
        self.jp_cards = {}
        self.term_mapping = defaultdict(set)
    
    def load_chinese_cards(self):
        """加载中文卡牌数据"""
        cn_file = self.base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        print(f"加载中文卡牌数据: {cn_file}")
        
        with open(cn_file, 'r', encoding='utf-8') as f:
            cards = json.load(f)
            for card in cards:
                card_no = card.get('card_no', '').upper()
                if card_no:
                    self.cn_cards[card_no] = card
        
        print(f"已加载 {len(self.cn_cards)} 张中文卡牌")
    
    def load_japanese_cards(self):
        """加载所有日文卡包数据"""
        print("加载日文卡牌数据...")
        
        jp_files = list(self.base_dir.glob("digimon_cards_*_cards.json"))
        
        for jp_file in jp_files:
            if "chiness" in str(jp_file):
                continue
                
            try:
                with open(jp_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_no = card.get('card_no', '').upper()
                        card_no = re.sub(r'_P\d+$', '', card_no)
                        if card_no and card_no not in self.jp_cards:
                            self.jp_cards[card_no] = card
            except Exception as e:
                print(f"读取文件 {jp_file.name} 时出错: {e}")
        
        print(f"已加载 {len(self.jp_cards)} 张日文卡牌")
    
    def extract_terms(self):
        """提取基础词汇"""
        print("\n开始提取基础词汇...")
        
        matched_count = 0
        
        for card_no, cn_card in self.cn_cards.items():
            normalized_no = card_no.replace('-', '').upper()
            
            jp_card = None
            if card_no in self.jp_cards:
                jp_card = self.jp_cards[card_no]
            elif normalized_no in self.jp_cards:
                jp_card = self.jp_cards[normalized_no]
            else:
                alt_no = card_no.replace('-', '') if '-' in card_no else f"{card_no[:2]}-{card_no[2:]}"
                if alt_no in self.jp_cards:
                    jp_card = self.jp_cards[alt_no]
            
            if jp_card:
                matched_count += 1
                self._extract_card_terms(cn_card, jp_card)
        
        print(f"成功匹配 {matched_count} 张卡牌")
        print(f"提取到 {len(self.term_mapping)} 个基础词汇")
    
    def _extract_card_terms(self, cn_card, jp_card):
        """从单张卡牌提取基础词汇"""
        # 1. 提取卡牌名称
        cn_name = cn_card.get('name_cn', '')
        jp_name = jp_card.get('card_name', '')
        # 移除日文卡名中的编号前缀
        jp_name = re.sub(r'^[A-Z0-9\-_]+', '', jp_name)
        
        if cn_name and jp_name:
            self.term_mapping[cn_name].add(jp_name)
        
        # 2. 提取卡牌类型
        cn_type = cn_card.get('type', '')
        jp_type = jp_card.get('card_type', '')
        if cn_type and jp_type:
            self.term_mapping[cn_type].add(jp_type)
        
        # 3. 提取颜色
        cn_color = cn_card.get('color', '')
        jp_color = jp_card.get('color', '')
        if cn_color and jp_color:
            # 处理多颜色卡牌
            cn_colors = [c.strip() for c in cn_color.split('/')]
            jp_colors = [c.strip() for c in jp_color.split('/')]
            
            # 如果颜色数量相同，建立对应关系
            if len(cn_colors) == len(jp_colors):
                for cn_c, jp_c in zip(cn_colors, jp_colors):
                    if cn_c and jp_c:
                        self.term_mapping[cn_c].add(jp_c)
        
        # 4. 提取形态
        cn_form = cn_card.get('form', '')
        jp_form = jp_card.get('form', '')
        if cn_form and jp_form:
            self.term_mapping[cn_form].add(jp_form)
        
        # 5. 提取属性
        cn_attr = cn_card.get('attribute', '')
        jp_attr = jp_card.get('attribute', '')
        if cn_attr and jp_attr:
            self.term_mapping[cn_attr].add(jp_attr)
        
        # 6. 提取稀有度
        cn_rarity = cn_card.get('rarity', '')
        jp_rarity = jp_card.get('rarity', '')
        if cn_rarity and jp_rarity:
            self.term_mapping[cn_rarity].add(jp_rarity)
    
    def save_mapping(self, output_file):
        """保存基础词汇对照表"""
        print(f"\n保存基础词汇对照表到: {output_file}")
        
        # 转换为可序列化的格式
        mapping_dict = {}
        for cn_term, jp_terms in sorted(self.term_mapping.items()):
            mapping_dict[cn_term] = sorted(list(jp_terms))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_dict, f, ensure_ascii=False, indent=2)
        
        print(f"基础词汇对照表已保存，共 {len(mapping_dict)} 个词条")
    
    def generate_report(self, output_file):
        """生成统计报告"""
        print(f"\n生成统计报告: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 数码宝贝卡牌基础词汇对照统计报告\n\n")
            f.write(f"## 数据统计\n\n")
            f.write(f"- 中文卡牌总数: {len(self.cn_cards)}\n")
            f.write(f"- 日文卡牌总数: {len(self.jp_cards)}\n")
            f.write(f"- 基础词汇数: {len(self.term_mapping)}\n\n")
            
            f.write(f"## 提取内容\n\n")
            f.write(f"本工具只提取以下基础特征：\n")
            f.write(f"- 卡牌名称（数码兽名称）\n")
            f.write(f"- 卡牌类型（数码兽卡、数码蛋卡、驯兽师卡、选项卡）\n")
            f.write(f"- 颜色（红、蓝、黄、绿、黑、紫、白）\n")
            f.write(f"- 形态（幼年期、成长期、成熟期、完全体、究极体）\n")
            f.write(f"- 属性（疫苗、数据、病毒等）\n")
            f.write(f"- 稀有度（C、U、R、SR等）\n\n")
            
            f.write(f"注意: 如需游戏机制关键词，请使用 extract_game_mechanics_only.py\n\n")
            
            f.write(f"## 词汇分类示例\n\n")
            
            # 按类别展示部分词汇
            categories = {
                '颜色': ['红', '蓝', '黄', '绿', '黑', '紫', '白'],
                '形态': ['幼年期', '成长期', '成熟期', '完全体', '究极体', '应用兽'],
                '属性': ['疫苗', '数据', '病毒', '自由', '可变', '不明'],
                '卡牌类型': ['数码兽卡', '数码蛋卡', '驯兽师卡', '选项卡'],
                '稀有度': ['C', 'U', 'R', 'SR', 'SEC', 'P'],
            }
            
            for category, terms in categories.items():
                f.write(f"### {category}\n\n")
                f.write("| 中文 | 日文 |\n")
                f.write("|------|------|\n")
                for term in terms:
                    if term in self.term_mapping:
                        jp_terms = ', '.join(sorted(self.term_mapping[term]))
                        f.write(f"| {term} | {jp_terms} |\n")
                f.write("\n")
        
        print("统计报告已生成")


def main():
    base_dir = Path(__file__).parent.parent
    
    print("=" * 60)
    print("数码宝贝卡牌基础词汇提取工具")
    print("=" * 60)
    
    extractor = BasicTermExtractor(base_dir)
    
    extractor.load_chinese_cards()
    extractor.load_japanese_cards()
    extractor.extract_terms()
    
    output_dir = Path(__file__).parent
    extractor.save_mapping(output_dir / "basic_terms_cn_jp.json")
    extractor.generate_report(output_dir / "basic_terms_report.md")
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("生成文件:")
    print("  - basic_terms_cn_jp.json (基础词汇对照表)")
    print("  - basic_terms_report.md (统计报告)")
    print("\n提示: 如需游戏机制关键词，请运行:")
    print("  python extract_game_mechanics_only.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
