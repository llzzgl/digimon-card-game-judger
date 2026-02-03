"""
日文QA翻译脚本
使用术语表和卡牌数据库进行准确的专有名词翻译
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import time

# 可选：使用Google Translate API或其他翻译服务
try:
    from googletrans import Translator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    print("警告: googletrans未安装，将只进行术语替换，不进行机器翻译")
    print("安装方法: pip install googletrans==4.0.0-rc1")


class QATranslator:
    def __init__(self, 
                 terminology_path: str,
                 card_data_path: str,
                 input_qa_path: str,
                 output_qa_path: str):
        """
        初始化翻译器
        
        Args:
            terminology_path: 术语表JSON路径
            card_data_path: 中文卡牌数据JSON路径
            input_qa_path: 输入的日文QA JSON路径
            output_qa_path: 输出的中文QA JSON路径
        """
        self.terminology_path = Path(terminology_path)
        self.card_data_path = Path(card_data_path)
        self.input_qa_path = Path(input_qa_path)
        self.output_qa_path = Path(output_qa_path)
        
        # 加载数据
        self.terminology = self._load_terminology()
        self.card_mapping = self._load_card_mapping()
        
        # 初始化翻译器
        if HAS_TRANSLATOR:
            self.translator = Translator()
        else:
            self.translator = None
    
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
    
    def _replace_terminology(self, text: str) -> str:
        """替换文本中的专有术语"""
        if not text:
            return text
        
        result = text
        # 按长度降序排序，优先匹配长术语
        sorted_terms = sorted(self.terminology.items(), 
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
    
    def _translate_text(self, text: str) -> str:
        """使用机器翻译API翻译文本"""
        if not text or not self.translator:
            return text
        
        try:
            # 翻译日文到中文
            translated = self.translator.translate(text, src='ja', dest='zh-cn')
            return translated.text
        except Exception as e:
            print(f"翻译失败: {e}")
            return text
    
    def translate_qa_item(self, qa_item: Dict) -> Dict:
        """翻译单个QA条目"""
        translated = qa_item.copy()
        
        # 获取卡号
        card_no = qa_item.get('card_no', '')
        
        # 翻译问题
        question = qa_item.get('question', '')
        if question:
            # 1. 先进行机器翻译（如果可用）
            if self.translator:
                question = self._translate_text(question)
            
            # 2. 替换专有术语
            question = self._replace_terminology(question)
            
            # 3. 替换卡牌名称
            question = self._replace_card_names(question, card_no)
            
            translated['question'] = question
        
        # 翻译答案
        answer = qa_item.get('answer', '')
        if answer:
            # 1. 先进行机器翻译（如果可用）
            if self.translator:
                answer = self._translate_text(answer)
            
            # 2. 替换专有术语
            answer = self._replace_terminology(answer)
            
            # 3. 替换卡牌名称
            answer = self._replace_card_names(answer, card_no)
            
            translated['answer'] = answer
        
        # 翻译卡牌名称字段
        if 'card_name' in qa_item and card_no:
            if card_no in self.card_mapping:
                card_info = self.card_mapping[card_no]
                translated['card_name'] = f"{card_no} {card_info['name_cn']}"
        
        # 更新语言标记
        translated['language'] = 'zh-cn'
        translated['translated_from'] = 'ja'
        
        return translated
    
    def translate_all(self, batch_size: int = 10, delay: float = 1.0):
        """
        翻译所有QA条目
        
        Args:
            batch_size: 每批处理的数量
            delay: 每批之间的延迟（秒），避免API限流
        """
        # 加载日文QA
        print(f"\n正在加载日文QA: {self.input_qa_path}")
        with open(self.input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        print(f"✓ 加载了 {len(qa_list)} 条QA")
        
        # 翻译
        translated_list = []
        total = len(qa_list)
        
        print(f"\n开始翻译...")
        for i, qa_item in enumerate(qa_list, 1):
            try:
                translated = self.translate_qa_item(qa_item)
                translated_list.append(translated)
                
                # 显示进度
                if i % 10 == 0 or i == total:
                    print(f"进度: {i}/{total} ({i*100//total}%)")
                
                # 批次延迟
                if self.translator and i % batch_size == 0 and i < total:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"翻译第 {i} 条QA时出错: {e}")
                # 保留原始数据
                translated_list.append(qa_item)
        
        # 保存结果
        print(f"\n正在保存翻译结果: {self.output_qa_path}")
        self.output_qa_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_qa_path, 'w', encoding='utf-8') as f:
            json.dump(translated_list, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 翻译完成！共翻译 {len(translated_list)} 条QA")
        print(f"✓ 输出文件: {self.output_qa_path}")


def main():
    """主函数"""
    # 设置路径
    base_dir = Path(__file__).parent.parent.parent
    
    terminology_path = base_dir / "digimon_data" / "dtcg_terminology.json"
    card_data_path = base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
    input_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_jp.json"
    output_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_cn.json"
    
    # 创建翻译器
    translator = QATranslator(
        terminology_path=str(terminology_path),
        card_data_path=str(card_data_path),
        input_qa_path=str(input_qa_path),
        output_qa_path=str(output_qa_path)
    )
    
    # 执行翻译
    translator.translate_all(batch_size=10, delay=1.0)


if __name__ == "__main__":
    main()
