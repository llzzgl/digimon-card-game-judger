"""
智能关键词提取 - 基于规则和模式匹配
利用中文文本中的日文原文（括号内容）来建立对照关系
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter


class SmartKeywordExtractor:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.cn_cards = {}
        self.jp_cards = {}
        self.keywords = defaultdict(set)
        
        # 游戏机制相关的模式
        self.patterns = {
            # 【xxx时】模式
            'timing': re.compile(r'【([^】]+时)】'),
            # 【xxx】能力关键词
            'ability': re.compile(r'【([^】]+)】(?![时]|[0-9])'),
            # 特征中包含「xxx（yyy）」
            'trait': re.compile(r'特征中[包持有]+「([^「」（）]+)（([^（）]+)）」'),
            # 名称包含「xxx（yyy）」
            'name_pattern': re.compile(r'名称[包含]+「([^「」（）]+)（([^（）]+)）」'),
            # xxx（yyy）一般模式
            'general': re.compile(r'([^（）「」【】\d]+)（([^（）]+)）'),
            # 数值相关：DP、Lv、费用等
            'value': re.compile(r'(DP|Lv|费用|内存值|登场费用|进化费用)'),
            # 区域相关
            'zone': re.compile(r'(手牌|卡组|废弃区|安防区|战斗区域|育成区域|进化源)'),
            # 动作相关
            'action': re.compile(r'(登场|进化|攻击|消灭|丢弃|抽卡|放置|返回|激活|休眠|退化|孵化|判定|变更|公开|选择)'),
        }
    
    def load_chinese_cards(self):
        """加载中文卡牌数据"""
        cn_file = self.base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        print(f"加载中文卡牌数据: {cn_file}")
        print(f"文件存在: {cn_file.exists()}")
        
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
        
        # 如果没找到，尝试相对于脚本的路径
        if not jp_files:
            jp_files = list((Path(__file__).parent.parent).glob("digimon_cards_*_cards.json"))
        
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
    
    def extract_from_brackets(self, text):
        """从括号中提取中日文对照"""
        pairs = []
        
        # 特征中包含「xxx（yyy）」
        for match in self.patterns['trait'].finditer(text):
            cn_term = match.group(1).strip()
            jp_term = match.group(2).strip()
            if cn_term and jp_term and not any(char.isdigit() for char in cn_term):
                pairs.append((cn_term, jp_term, 'trait'))
        
        # 名称包含「xxx（yyy）」
        for match in self.patterns['name_pattern'].finditer(text):
            cn_term = match.group(1).strip()
            jp_term = match.group(2).strip()
            if cn_term and jp_term and not any(char.isdigit() for char in cn_term):
                pairs.append((cn_term, jp_term, 'name'))
        
        # 一般的 xxx（yyy）模式
        for match in self.patterns['general'].finditer(text):
            cn_term = match.group(1).strip()
            jp_term = match.group(2).strip()
            
            # 过滤条件
            if not cn_term or not jp_term:
                continue
            if len(cn_term) < 2 or len(jp_term) < 2:
                continue
            if any(char.isdigit() for char in cn_term):
                continue
            # 排除卡牌名称（通常较长）
            if len(cn_term) > 10:
                continue
            
            pairs.append((cn_term, jp_term, 'general'))
        
        return pairs
    
    def extract_timing_keywords(self, text):
        """提取时机关键词【xxx时】"""
        keywords = []
        for match in self.patterns['timing'].finditer(text):
            keyword = match.group(1).strip()
            if keyword:
                keywords.append((keyword, 'timing'))
        return keywords
    
    def extract_ability_keywords(self, text):
        """提取能力关键词【xxx】"""
        keywords = []
        for match in self.patterns['ability'].finditer(text):
            keyword = match.group(1).strip()
            # 过滤掉时机关键词和数字
            if keyword and not keyword.endswith('时') and not any(char.isdigit() for char in keyword):
                # 只保留常见的能力关键词长度
                if 2 <= len(keyword) <= 8:
                    keywords.append((keyword, 'ability'))
        return keywords
    
    def extract_game_terms(self, text):
        """提取游戏术语"""
        terms = []
        
        # 数值相关
        for match in self.patterns['value'].finditer(text):
            term = match.group(1)
            terms.append((term, 'value'))
        
        # 区域相关
        for match in self.patterns['zone'].finditer(text):
            term = match.group(1)
            terms.append((term, 'zone'))
        
        # 动作相关
        for match in self.patterns['action'].finditer(text):
            term = match.group(1)
            terms.append((term, 'action'))
        
        return terms
    
    def extract_keywords(self):
        """提取关键词"""
        print("\n开始智能提取关键词...")
        
        matched_count = 0
        bracket_pairs = defaultdict(lambda: defaultdict(int))
        timing_keywords = defaultdict(int)
        ability_keywords = defaultdict(int)
        game_terms = defaultdict(int)
        
        for card_no, cn_card in self.cn_cards.items():
            normalized_no = card_no.replace('-', '').upper()
            
            jp_card = None
            if card_no in self.jp_cards:
                jp_card = self.jp_cards[card_no]
            elif normalized_no in self.jp_cards:
                jp_card = self.jp_cards[normalized_no]
            
            if not jp_card:
                continue
            
            matched_count += 1
            
            # 检查所有效果字段
            effect_fields = ['effect', 'inherited_effect', 'security_effect']
            
            for field in effect_fields:
                cn_text = cn_card.get(field, '')
                jp_text = jp_card.get(field, '')
                
                if not cn_text:
                    continue
                
                # 1. 从括号中提取对照
                pairs = self.extract_from_brackets(cn_text)
                for cn_term, jp_term, category in pairs:
                    bracket_pairs[cn_term][jp_term] += 1
                
                # 2. 提取时机关键词
                timings = self.extract_timing_keywords(cn_text)
                for keyword, _ in timings:
                    timing_keywords[keyword] += 1
                
                # 3. 提取能力关键词
                abilities = self.extract_ability_keywords(cn_text)
                for keyword, _ in abilities:
                    ability_keywords[keyword] += 1
                
                # 4. 提取游戏术语
                terms = self.extract_game_terms(cn_text)
                for term, _ in terms:
                    game_terms[term] += 1
        
        print(f"成功匹配 {matched_count} 张卡牌")
        
        # 整理结果
        # 1. 括号对照（最可靠）
        for cn_term, jp_terms in bracket_pairs.items():
            # 选择出现次数最多的日文对照
            most_common_jp = max(jp_terms.items(), key=lambda x: x[1])[0]
            self.keywords[cn_term].add(most_common_jp)
        
        # 2. 时机关键词（需要匹配日文）
        timing_map = {
            '登场时': '登場時',
            '进化时': '進化時',
            '攻击时': 'アタック時',
            '消灭时': '破棄時',
            '移动时': 'ムーブ時',
            '回合开始时': 'ターン開始時',
            '回合结束时': 'ターン終了時',
            '主要阶段开始时': 'メインフェイズ開始時',
            '攻击结束时': 'アタック終了時',
        }
        for cn_kw, count in timing_keywords.items():
            if count >= 3 and cn_kw in timing_map:  # 至少出现3次
                self.keywords[cn_kw].add(timing_map[cn_kw])
        
        # 3. 能力关键词（需要匹配日文）
        ability_map = {
            '贯通': '貫通',
            '突进': '突進',
            '干扰': 'ジャミング',
            '阻挡者': 'ブロッカー',
            '再启动': 'リブート',
            '安防攻击': 'セキュリティアタック',
            '冲突': 'ラッシュ',
            '超频': 'オーバーフロー',
            '不屈': '不屈',
            '回避': '回避',
            '解码': 'デコード',
        }
        for cn_kw, count in ability_keywords.items():
            if count >= 3 and cn_kw in ability_map:
                self.keywords[cn_kw].add(ability_map[cn_kw])
        
        # 4. 游戏术语（需要匹配日文）
        term_map = {
            'DP': 'DP',
            'Lv': 'Lv',
            '费用': 'コスト',
            '内存值': 'メモリ',
            '登场费用': '登場コスト',
            '进化费用': '進化コスト',
            '手牌': '手札',
            '卡组': 'デッキ',
            '废弃区': 'トラッシュ',
            '安防区': 'セキュリティ',
            '战斗区域': 'バトルエリア',
            '育成区域': '育成エリア',
            '进化源': '進化元',
            '登场': '登場',
            '进化': '進化',
            '攻击': 'アタック',
            '消灭': '破棄',
            '休眠': 'レスト',
            '激活': 'アクティブ',
        }
        for cn_term, count in game_terms.items():
            if count >= 5 and cn_term in term_map:
                self.keywords[cn_term].add(term_map[cn_term])
        
        print(f"提取到 {len(self.keywords)} 个关键词")
        
        # 打印统计
        print(f"\n统计信息:")
        print(f"  - 从括号提取: {len(bracket_pairs)} 个")
        print(f"  - 时机关键词: {len([k for k in timing_keywords if timing_keywords[k] >= 3])} 个")
        print(f"  - 能力关键词: {len([k for k in ability_keywords if ability_keywords[k] >= 3])} 个")
        print(f"  - 游戏术语: {len([k for k in game_terms if game_terms[k] >= 5])} 个")
    
    def save_keywords(self, output_file):
        """保存关键词"""
        print(f"\n保存关键词到: {output_file}")
        
        keywords_dict = {}
        for cn_kw, jp_kws in sorted(self.keywords.items()):
            keywords_dict[cn_kw] = sorted(list(jp_kws))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(keywords_dict, f, ensure_ascii=False, indent=2)
        
        print(f"关键词已保存，共 {len(keywords_dict)} 个词条")
    
    def generate_report(self, output_file):
        """生成报告"""
        print(f"\n生成报告: {output_file}")
        
        # 按类别分类
        categories = {
            'timing': [],
            'ability': [],
            'zone': [],
            'action': [],
            'value': [],
            'trait': [],
            'other': []
        }
        
        timing_keywords = ['时', '阶段']
        ability_keywords = ['贯通', '突进', '干扰', '阻挡', '启动', '攻击', '冲突', '频', '屈', '避', '解码']
        zone_keywords = ['手牌', '卡组', '废弃', '安防', '战斗', '育成', '进化源']
        action_keywords = ['登场', '进化', '攻击', '消灭', '丢弃', '抽', '放置', '返回', '激活', '休眠', '退化', '孵化', '判定', '变更', '公开', '选择']
        value_keywords = ['DP', 'Lv', '费用', '内存']
        
        for cn_kw in sorted(self.keywords.keys()):
            if any(kw in cn_kw for kw in timing_keywords):
                categories['timing'].append(cn_kw)
            elif any(kw in cn_kw for kw in ability_keywords):
                categories['ability'].append(cn_kw)
            elif any(kw in cn_kw for kw in zone_keywords):
                categories['zone'].append(cn_kw)
            elif any(kw in cn_kw for kw in action_keywords):
                categories['action'].append(cn_kw)
            elif any(kw in cn_kw for kw in value_keywords):
                categories['value'].append(cn_kw)
            elif '型' in cn_kw or '者' in cn_kw or '兽' in cn_kw:
                categories['trait'].append(cn_kw)
            else:
                categories['other'].append(cn_kw)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 智能提取的中日文关键词对照表\n\n")
            f.write("本表通过智能分析卡牌效果文本自动提取，包含括号中的日文原文对照。\n\n")
            
            category_names = {
                'timing': '效果触发时机',
                'ability': '关键词能力',
                'zone': '游戏区域',
                'action': '游戏动作',
                'value': '数值相关',
                'trait': '特征/种族',
                'other': '其他术语',
            }
            
            total = 0
            for cat_key, cat_name in category_names.items():
                keywords = categories[cat_key]
                if not keywords:
                    continue
                
                f.write(f"## {cat_name} ({len(keywords)}个)\n\n")
                f.write("| 中文 | 日文 |\n")
                f.write("|------|------|\n")
                
                for cn_kw in keywords:
                    jp_terms = ', '.join(sorted(self.keywords[cn_kw]))
                    f.write(f"| {cn_kw} | {jp_terms} |\n")
                    total += 1
                
                f.write("\n")
            
            f.write(f"## 总计\n\n")
            f.write(f"共 {total} 个关键词\n")
        
        print("报告已生成")


def main():
    # 脚本在 term_mapping 目录，需要上一级到 digimon_card_data
    script_dir = Path(__file__).resolve().parent  # term_mapping
    base_dir = script_dir.parent  # digimon_card_data
    
    print("=" * 60)
    print("智能关键词提取工具")
    print("基于规则和模式匹配，利用括号中的日文原文")
    print("=" * 60)
    print(f"脚本目录: {script_dir}")
    print(f"数据目录: {base_dir}")
    print()
    
    extractor = SmartKeywordExtractor(base_dir)
    
    extractor.load_chinese_cards()
    extractor.load_japanese_cards()
    extractor.extract_keywords()
    
    output_dir = script_dir
    extractor.save_keywords(output_dir / "smart_keywords_cn_jp.json")
    extractor.generate_report(output_dir / "smart_keywords_report.md")
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("生成文件:")
    print("  - smart_keywords_cn_jp.json (智能提取的关键词)")
    print("  - smart_keywords_report.md (分类报告)")
    print("=" * 60)


if __name__ == "__main__":
    main()
