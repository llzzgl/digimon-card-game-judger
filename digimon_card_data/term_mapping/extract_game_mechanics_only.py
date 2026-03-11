"""
只提取游戏机制关键词
不提取卡牌名称、数码兽名称等内容
"""

import json
import re
from pathlib import Path
from collections import defaultdict


class GameMechanicsExtractor:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.cn_cards = {}
        self.jp_cards = {}
        self.keywords = defaultdict(set)
        
        # 定义游戏机制关键词
        self.game_mechanics = self._init_game_mechanics()
    
    def _init_game_mechanics(self):
        """定义游戏机制关键词（只包含真正的游戏术语）"""
        return {
            # 效果触发时机
            'timing': [
                ('登场时', '登場時'),
                ('进化时', '進化時'),
                ('攻击时', 'アタック時'),
                ('消灭时', '破棄時'),
                ('移动时', 'ムーブ時'),
                ('回合开始时', 'ターン開始時'),
                ('回合结束时', 'ターン終了時'),
                ('主要阶段开始时', 'メインフェイズ開始時'),
                ('攻击结束时', 'アタック終了時'),
                ('自己的回合', '自分のターン'),
                ('对手的回合', '相手のターン'),
                ('双方的回合', 'お互いのターン'),
                ('自己主要阶段开始时', '自分のメインフェイズ開始時'),
                ('对手的回合结束时', '相手のターン終了時'),
                ('自己的回合开始时', '自分のターン開始時'),
            ],
            
            # 游戏动作
            'actions': [
                ('登场', '登場'),
                ('进化', '進化'),
                ('攻击', 'アタック'),
                ('消灭', '破棄'),
                ('丢弃', '捨てる'),
                ('抽卡', 'ドロー'),
                ('放置', '置く'),
                ('返回', '戻す'),
                ('激活', 'アクティブ'),
                ('休眠', 'レスト'),
                ('退化', '退化'),
                ('孵化', 'ハッチ'),
                ('连接', 'ジョグレス'),
                ('判定', 'チェック'),
                ('变更', '変更'),
                ('公开', '公開'),
                ('选择', '選ぶ'),
            ],
            
            # 游戏区域
            'zones': [
                ('手牌', '手札'),
                ('卡组', 'デッキ'),
                ('废弃区', 'トラッシュ'),
                ('安防区', 'セキュリティ'),
                ('战斗区域', 'バトルエリア'),
                ('育成区域', '育成エリア'),
                ('进化源', '進化元'),
                ('最上方', '一番上'),
                ('最下方', '一番下'),
                ('叠放卡', 'カード'),
            ],
            
            # 关键词能力
            'abilities': [
                ('贯通', '貫通'),
                ('突进', '突進'),
                ('干扰', 'ジャミング'),
                ('阻挡者', 'ブロッカー'),
                ('再启动', 'リブート'),
                ('安防攻击', 'セキュリティアタック'),
                ('冲突', 'ラッシュ'),
                ('超频', 'オーバーフロー'),
                ('联合攻击', 'ジョグレス'),
                ('替罪羊', 'スケープゴート'),
                ('同行', 'パートナー'),
                ('不屈', '不屈'),
                ('回避', '回避'),
                ('解码', 'デコード'),
                ('碎片', 'フラグメント'),
                ('冰装', 'アイスクラッド'),
                ('旋风', 'サイクロン'),
                ('处决', '処刑'),
                ('防护墙', 'バリア'),
                ('速攻', 'スピード'),
                ('诱导', 'インデュース'),
                ('旋风阻挡者', 'サイクロンブロッカー'),
            ],
            
            # 数值相关
            'values': [
                ('DP', 'DP'),
                ('Lv', 'Lv'),
                ('费用', 'コスト'),
                ('内存值', 'メモリ'),
                ('登场费用', '登場コスト'),
                ('进化费用', '進化コスト'),
            ],
            
            # 卡牌类型
            'card_types': [
                ('数码兽', 'デジモン'),
                ('驯兽师', 'テイマー'),
                ('选项', 'オプション'),
                ('数码蛋', 'デジタマ'),
            ],
            
            # 其他常见术语
            'other': [
                ('1回合1次', '1ターンに1回'),
                ('不支付费用', 'コストを支払わずに'),
                ('背面表示', '裏向き'),
                ('正面表示', '表向き'),
                ('安防能力', 'セキュリティ'),
            ]
        }
    
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
    
    def extract_keywords(self):
        """提取关键词 - 直接使用预定义的关键词列表"""
        print("\n开始提取游戏机制关键词...")
        
        # 直接使用预定义的所有关键词
        for category, keywords in self.game_mechanics.items():
            for cn_kw, jp_kw in keywords:
                self.keywords[cn_kw].add(jp_kw)
        
        print(f"提取到 {len(self.keywords)} 个游戏机制关键词")
    
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
        """生成分类报告"""
        print(f"\n生成分类报告: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 数码宝贝卡牌游戏机制关键词对照表\n\n")
            f.write("本表只包含游戏机制相关的关键词，不包含卡牌名称、数码兽名称等内容。\n\n")
            
            total_count = 0
            for category, keywords in self.game_mechanics.items():
                category_names = {
                    'timing': '效果触发时机',
                    'actions': '游戏动作',
                    'zones': '游戏区域',
                    'abilities': '关键词能力',
                    'values': '数值相关',
                    'card_types': '卡牌类型',
                    'other': '其他术语',
                }
                
                f.write(f"## {category_names.get(category, category)} ({len(keywords)}个)\n\n")
                f.write("| 中文 | 日文 |\n")
                f.write("|------|------|\n")
                
                for cn_kw, jp_kw in keywords:
                    jp_terms = ', '.join(sorted(self.keywords[cn_kw]))
                    f.write(f"| {cn_kw} | {jp_terms} |\n")
                    total_count += 1
                
                f.write("\n")
            
            f.write(f"## 总计\n\n")
            f.write(f"共 {total_count} 个游戏机制关键词\n")
        
        print("分类报告已生成")


def main():
    base_dir = Path(__file__).parent.parent
    
    print("=" * 60)
    print("数码宝贝卡牌游戏机制关键词提取工具")
    print("=" * 60)
    
    extractor = GameMechanicsExtractor(base_dir)
    
    # 不再需要加载卡牌数据，直接使用预定义的关键词
    extractor.extract_keywords()
    
    output_dir = Path(__file__).parent
    extractor.save_keywords(output_dir / "game_mechanics_keywords.json")
    extractor.generate_report(output_dir / "game_mechanics_report.md")
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("生成文件:")
    print("  - game_mechanics_keywords.json (游戏机制关键词)")
    print("  - game_mechanics_report.md (分类报告)")
    print("=" * 60)


if __name__ == "__main__":
    main()
