"""
日文QA翻译脚本 - 本地版本
仅使用术语表和卡牌数据库，不依赖外部翻译API
适合快速处理专有名词替换
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class LocalQATranslator:
    def __init__(self, 
                 terminology_path: str,
                 card_data_path: str,
                 input_qa_path: str,
                 output_qa_path: str):
        """
        初始化本地翻译器
        
        Args:
            terminology_path: 术语表JSON路径
            card_data_path: 中文卡牌数据JSON路径
            input_qa_path: 输入的日文QA JSON路径
            output_qa_path: 输出的处理后QA JSON路径
        """
        self.terminology_path = Path(terminology_path)
        self.card_data_path = Path(card_data_path)
        self.input_qa_path = Path(input_qa_path)
        self.output_qa_path = Path(output_qa_path)
        
        # 加载数据
        self.terminology = self._load_terminology()
        self.card_mapping = self._load_card_mapping()
        
        # 构建常见游戏术语映射
        self.game_terms = self._build_game_terms()
    
    def _load_terminology(self) -> Dict[str, str]:
        """加载术语表，构建日文->中文映射"""
        with open(self.terminology_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 展平所有术语到一个字典
        term_map = {}
        for category, terms in data.items():
            if isinstance(terms, dict):
                term_map.update(terms)
        
        print(f"✓ 加载了 {len(term_map)} 个术语")
        return term_map
    
    def _load_card_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载卡牌数据，构建卡号->卡牌信息的映射"""
        with open(self.card_data_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        # 按卡号建立索引
        card_map = {}
        for card in cards:
            card_no = card.get('card_no', '')
            if card_no:
                card_map[card_no] = {
                    'name_cn': card.get('name_cn', ''),
                    'name_jp': card.get('name_jp', ''),
                    'card_no': card_no
                }
        
        print(f"✓ 加载了 {len(card_map)} 张卡牌数据")
        return card_map
    
    def _build_game_terms(self) -> Dict[str, str]:
        """构建常见游戏术语映射"""
        return {
            # 效果相关
            '【登場時】': '【登场时】',
            '【進化時】': '【进化时】',
            '【アタック時】': '【攻击时】',
            '【相手のターン】': '【对手的回合】',
            '【自分のターン】': '【自己的回合】',
            '【メインフェイズ】': '【主要阶段】',
            '【セキュリティ】': '【安防】',
            '【消滅時】': '【消灭时】',
            '【ドロー時】': '【抽卡时】',
            
            # 状态
            'アクティブ状態': '激活状态',
            'レスト状態': '休眠状态',
            'アクティブ': '激活',
            'レスト': '休眠',
            
            # 区域
            'バトルエリア': '战斗区域',
            'セキュリティ': '安防',
            'トラッシュ': '废弃区',
            'デッキ': '牌组',
            '手札': '手牌',
            '育成エリア': '培育区域',
            
            # 动作
            'アタックすること': '攻击',
            'アタックした': '攻击了',
            'アタックし': '攻击',
            'アタック': '攻击',
            'ブロック': '阻挡',
            'チェックした': '检查了',
            'チェックされた': '被检查',
            'チェック': '检查',
            '発揮されます': '发动',
            '発揮させます': '发动',
            '発揮した': '发动了',
            '発揮': '发动',
            '誘発した': '触发了',
            '誘発': '触发',
            '消滅します': '消灭',
            '消滅': '消灭',
            '破棄': '丢弃',
            '登場': '登场',
            '進化': '进化',
            'ドロー': '抽卡',
            '変更すること': '变更',
            '変更': '变更',
            '選ぶこと': '选择',
            '選べなく': '不能选择',
            '選ばれなかった': '未被选择的',
            '選ばれ': '被选择',
            '選ぶ': '选择',
            
            # 数值
            'DP': 'DP',
            'コスト': '费用',
            '登場コスト': '登场费用',
            '進化コスト': '进化费用',
            'メモリー': '记忆值',
            
            # 卡牌相关
            'このカード': '这张卡',
            'カード': '卡牌',
            'デジモン': '数码宝贝',
            'テイマー': '驯兽师',
            'オプション': '选项',
            'デジタマ': '数码蛋',
            
            # 玩家相关
            'ターンプレイヤー側': '回合玩家方',
            'ターンプレイヤー': '回合玩家',
            '相手の': '对手的',
            '自分の': '自己的',
            '相手': '对手',
            '自分': '自己',
            
            # 疑问句和常用句式
            'することができますか': '可以吗',
            'できますか': '可以吗',
            'どうなりますか': '会怎样',
            'ことができます': '可以',
            'ことはできず': '无法',
            'できません': '不可以',
            'できます': '可以',
            'できる': '可以',
            'できない': '不可以',
            
            # 疑问词
            'どの順で': '按什么顺序',
            'どの': '哪个',
            'どちらの': '哪边的',
            'どちら': '哪边',
            'いつ': '何时',
            
            # 回答词
            'はい、': '是的，',
            'いいえ、': '不，',
            'はい': '是的',
            'いいえ': '不',
            
            # 连接词和助词
            'した場合': '的情况下',
            'した場合、': '的情况下，',
            'したとき': '时',
            'したとき、': '时，',
            'したあとに': '之后',
            'したあとに、': '之后，',
            'する場合': '的情况',
            'する場合、': '的情况，',
            'のとき': '的时候',
            'のときは': '的时候',
            'のとき、': '的时候，',
            'があるとき': '存在时',
            'があるときは': '存在时',
            'があるとき、': '存在时，',
            'にあるとき': '存在时',
            'にあるときは': '存在时',
            'にあるとき、': '存在时，',
            'が同時に': '同时',
            'が同時にある': '同时存在',
            'が同時にあるとき': '同时存在时',
            'が同時誘発': '同时触发',
            'が減った': '减少了',
            'が減ったとき': '减少时',
            
            # 状态描述
            'がいる状況です': '存在的情况',
            'がいる状況': '存在的情况',
            'がある状況です': '存在的情况',
            'がある状況': '存在的情况',
            'にいる': '在',
            'がいる': '存在',
            'がある': '有',
            'がない': '没有',
            'のみが': '仅',
            'のみ': '仅',
            'だけ': '只',
            'しか': '只',
            
            # 形容词和副词
            '優先して': '优先',
            '優先': '优先',
            '即座に': '立即',
            '即座': '立即',
            '全ての': '所有的',
            '全て': '全部',
            'それ以外の': '其他的',
            'それ以外': '其他',
            
            # 动词变形
            'されます': '',
            'させます': '',
            'します': '',
            'なります': '变为',
            'ならずに': '不会',
            'なる': '变为',
            'ない': '不',
            'なかった': '没有',
            
            # 其他常用词
            '場合': '情况',
            '状況': '情况',
            '効果': '效果',
            '目標': '目标',
            '宣言': '宣言',
            '可能です': '可能',
            '可能': '可能',
            '不可能': '不可能',
            '更新': '更新',
            
            # 特殊符号和标记
            'を': '',
            'に': '',
            'は': '',
            'が': '',
            'と': '和',
            'の': '的',
            'で': '',
            'から': '从',
            'まで': '到',
            'や': '和',
            'も': '也',
            'へ': '向',
        }
    
    def _replace_terms(self, text: str) -> str:
        """替换文本中的所有术语"""
        if not text:
            return text
        
        result = text
        
        # 合并所有术语
        all_terms = {**self.game_terms, **self.terminology}
        
        # 按长度降序排序，优先匹配长术语
        sorted_terms = sorted(all_terms.items(), 
                            key=lambda x: len(x[0]), 
                            reverse=True)
        
        for jp_term, cn_term in sorted_terms:
            result = result.replace(jp_term, cn_term)
        
        return result
    
    def _replace_card_names(self, text: str, card_no: Optional[str] = None) -> str:
        """替换文本中的卡牌名称"""
        if not text:
            return text
        
        result = text
        
        # 如果提供了卡号，优先使用该卡牌的名称
        if card_no and card_no in self.card_mapping:
            card_info = self.card_mapping[card_no]
            jp_name = card_info['name_jp']
            cn_name = card_info['name_cn']
            if jp_name and cn_name:
                result = result.replace(jp_name, cn_name)
        
        # 查找文本中的卡号模式 (如 "BT8-018", "EX11-010")
        card_no_pattern = r'([A-Z]{2,3}\d{1,2}-\d{3})'
        matches = re.findall(card_no_pattern, text)
        
        for matched_card_no in matches:
            if matched_card_no in self.card_mapping:
                card_info = self.card_mapping[matched_card_no]
                jp_name = card_info['name_jp']
                cn_name = card_info['name_cn']
                if jp_name and cn_name:
                    # 替换 "卡号 卡名" 格式
                    result = result.replace(f"{matched_card_no} {jp_name}", 
                                          f"{matched_card_no} {cn_name}")
                    # 也替换单独的卡名
                    result = result.replace(jp_name, cn_name)
        
        return result
    
    def translate_qa_item(self, qa_item: Dict) -> Dict:
        """处理单个QA条目"""
        processed = qa_item.copy()
        
        # 获取卡号
        card_no = qa_item.get('card_no', '')
        
        # 处理问题
        question = qa_item.get('question', '')
        if question:
            # 1. 替换专有术语和游戏术语
            question = self._replace_terms(question)
            
            # 2. 替换卡牌名称
            question = self._replace_card_names(question, card_no)
            
            processed['question'] = question
            processed['question_original'] = qa_item.get('question', '')
        
        # 处理答案
        answer = qa_item.get('answer', '')
        if answer:
            # 1. 替换专有术语和游戏术语
            answer = self._replace_terms(answer)
            
            # 2. 替换卡牌名称
            answer = self._replace_card_names(answer, card_no)
            
            processed['answer'] = answer
            processed['answer_original'] = qa_item.get('answer', '')
        
        # 处理卡牌名称字段
        if 'card_name' in qa_item and card_no:
            if card_no in self.card_mapping:
                card_info = self.card_mapping[card_no]
                processed['card_name'] = f"{card_no} {card_info['name_cn']}"
                processed['card_name_original'] = qa_item.get('card_name', '')
        
        # 更新语言标记
        processed['language'] = 'zh-cn'
        processed['translated_from'] = 'ja'
        processed['translation_method'] = 'terminology_replacement'
        
        return processed
    
    def translate_all(self):
        """处理所有QA条目"""
        # 加载日文QA
        print(f"\n正在加载日文QA: {self.input_qa_path}")
        with open(self.input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        print(f"✓ 加载了 {len(qa_list)} 条QA")
        
        # 处理
        processed_list = []
        total = len(qa_list)
        
        print(f"\n开始处理...")
        for i, qa_item in enumerate(qa_list, 1):
            try:
                processed = self.translate_qa_item(qa_item)
                processed_list.append(processed)
                
                # 显示进度
                if i % 50 == 0 or i == total:
                    print(f"进度: {i}/{total} ({i*100//total}%)")
                    
            except Exception as e:
                print(f"处理第 {i} 条QA时出错: {e}")
                # 保留原始数据
                processed_list.append(qa_item)
        
        # 保存结果
        print(f"\n正在保存处理结果: {self.output_qa_path}")
        self.output_qa_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_qa_path, 'w', encoding='utf-8') as f:
            json.dump(processed_list, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 处理完成！共处理 {len(processed_list)} 条QA")
        print(f"✓ 输出文件: {self.output_qa_path}")
        
        # 显示示例
        if processed_list:
            print("\n" + "="*60)
            print("示例 (第1条):")
            print("="*60)
            example = processed_list[0]
            print(f"\n原始问题:\n{example.get('question_original', '')}")
            print(f"\n处理后问题:\n{example.get('question', '')}")
            print(f"\n原始答案:\n{example.get('answer_original', '')}")
            print(f"\n处理后答案:\n{example.get('answer', '')}")


def main():
    """主函数"""
    # 设置路径
    base_dir = Path(__file__).parent.parent.parent
    
    terminology_path = base_dir / "digimon_data" / "dtcg_terminology.json"
    card_data_path = base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
    input_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_jp.json"
    output_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_cn.json"
    
    # 创建翻译器
    translator = LocalQATranslator(
        terminology_path=str(terminology_path),
        card_data_path=str(card_data_path),
        input_qa_path=str(input_qa_path),
        output_qa_path=str(output_qa_path)
    )
    
    # 执行处理
    translator.translate_all()


if __name__ == "__main__":
    main()
