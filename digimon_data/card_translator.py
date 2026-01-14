"""
DTCG 卡牌数据翻译器
将日文卡牌数据翻译成中文
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 导入术语表
from dtcg_terminology import (
    CARD_TYPE_MAPPING,
    COLOR_MAPPING,
    FORM_MAPPING,
    ATTRIBUTE_MAPPING,
    RARITY_MAPPING,
    KEYWORD_EFFECT_MAPPING,
    EFFECT_TIMING_MAPPING,
    GAME_TERM_MAPPING,
    DIGIMON_TYPE_MAPPING,
    get_all_mappings,
)

load_dotenv()


class CardTranslator:
    def __init__(self, 
                 name_mapping_path: Optional[str] = None,
                 use_ai: bool = True,
                 ai_provider: str = "gemini"):
        """
        初始化翻译器
        
        Args:
            name_mapping_path: 数码宝贝名称映射文件路径
            use_ai: 是否使用AI翻译效果文本
            ai_provider: AI提供商 ("gemini" 或 "openai")
        """
        self.name_mapping = {}
        self.terminology = get_all_mappings()
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.ai_model = None
        
        # 加载名称映射
        if name_mapping_path and Path(name_mapping_path).exists():
            self.load_name_mapping(name_mapping_path)
        
        # 初始化AI模型
        if use_ai:
            self._init_ai_model()
    
    def _init_ai_model(self):
        """初始化AI模型"""
        if self.ai_provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.ai_model = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Gemini AI 模型已初始化")
            except Exception as e:
                print(f"⚠️ Gemini 初始化失败: {e}")
                self.use_ai = False
        elif self.ai_provider == "openai":
            try:
                from openai import OpenAI
                self.ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                print("✅ OpenAI 模型已初始化")
            except Exception as e:
                print(f"⚠️ OpenAI 初始化失败: {e}")
                self.use_ai = False
    
    def load_name_mapping(self, path: str):
        """加载数码宝贝名称映射"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.name_mapping = json.load(f)
            print(f"✅ 已加载 {len(self.name_mapping)} 个名称映射")
        except Exception as e:
            print(f"⚠️ 加载名称映射失败: {e}")
    
    def translate_card_name(self, japanese_name: str) -> str:
        """
        翻译卡牌名称
        优先使用官方名称映射，否则保留原名
        """
        # 移除卡号前缀 (如 "ST1-01")
        clean_name = re.sub(r'^[A-Z]{2,3}\d+-\d+', '', japanese_name).strip()
        
        # 查找官方翻译
        if clean_name in self.name_mapping:
            return self.name_mapping[clean_name]
        
        # 尝试部分匹配
        for jpn, chn in self.name_mapping.items():
            if jpn in clean_name:
                return clean_name.replace(jpn, chn)
        
        # 无法翻译，返回原名
        return clean_name
    
    def translate_card_type(self, card_type: str) -> str:
        """翻译卡牌类型"""
        return CARD_TYPE_MAPPING.get(card_type, card_type)
    
    def translate_color(self, color: str) -> str:
        """翻译颜色"""
        if not color:
            return None
        return COLOR_MAPPING.get(color, color)
    
    def translate_form(self, form: str) -> str:
        """翻译形态"""
        if not form:
            return None
        return FORM_MAPPING.get(form, form)
    
    def translate_attribute(self, attribute: str) -> str:
        """翻译属性"""
        if not attribute:
            return None
        return ATTRIBUTE_MAPPING.get(attribute, attribute)
    
    def translate_digimon_type(self, digimon_type: str) -> str:
        """翻译数码宝贝类型"""
        if not digimon_type:
            return None
        return DIGIMON_TYPE_MAPPING.get(digimon_type, digimon_type)
    
    def translate_effect_text(self, text: str) -> str:
        """
        翻译效果文本
        先用术语表替换，再用AI翻译剩余部分
        """
        if not text:
            return None
        
        translated = text
        
        # 1. 替换关键词效果
        for jpn, chn in KEYWORD_EFFECT_MAPPING.items():
            translated = translated.replace(jpn, chn)
        
        # 2. 替换效果时机
        for jpn, chn in EFFECT_TIMING_MAPPING.items():
            translated = translated.replace(jpn, chn)
        
        # 3. 替换游戏术语
        for jpn, chn in GAME_TERM_MAPPING.items():
            translated = translated.replace(jpn, chn)
        
        # 4. 如果启用AI且文本中仍有日文，使用AI翻译
        if self.use_ai and self._contains_japanese(translated):
            translated = self._ai_translate_effect(translated)
        
        return translated
    
    def _contains_japanese(self, text: str) -> bool:
        """检查文本是否包含日文字符"""
        # 平假名: \u3040-\u309F
        # 片假名: \u30A0-\u30FF
        return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text))
    
    def _ai_translate_effect(self, text: str) -> str:
        """使用AI翻译效果文本"""
        prompt = f"""请将以下DTCG（数码宝贝卡牌游戏）效果文本翻译成中文。
注意：
1. 保持游戏术语的准确性
2. 已翻译的部分（如【登场时】、≪阻挡者≫等）保持不变
3. 数字和符号保持不变
4. 翻译要简洁准确

效果文本：
{text}

请直接输出翻译结果，不要添加任何说明。"""

        try:
            if self.ai_provider == "gemini" and self.ai_model:
                response = self.ai_model.generate_content(prompt)
                return response.text.strip()
            elif self.ai_provider == "openai" and hasattr(self, 'ai_client'):
                response = self.ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ AI翻译失败: {e}")
        
        return text  # 翻译失败返回原文
    
    def translate_card(self, card: dict) -> dict:
        """翻译单张卡牌"""
        translated = card.copy()
        
        # 翻译各字段
        if card.get('card_name'):
            translated['card_name_jp'] = card['card_name']  # 保留日文名
            translated['card_name'] = self.translate_card_name(card['card_name'])
        
        if card.get('card_type'):
            translated['card_type'] = self.translate_card_type(card['card_type'])
        
        if card.get('color'):
            translated['color'] = self.translate_color(card['color'])
        
        if card.get('color2'):
            translated['color2'] = self.translate_color(card['color2'])
        
        if card.get('form'):
            translated['form'] = self.translate_form(card['form'])
        
        if card.get('attribute'):
            translated['attribute'] = self.translate_attribute(card['attribute'])
        
        if card.get('digimon_type'):
            translated['digimon_type'] = self.translate_digimon_type(card['digimon_type'])
        
        if card.get('effect'):
            translated['effect_jp'] = card['effect']  # 保留日文效果
            translated['effect'] = self.translate_effect_text(card['effect'])
        
        if card.get('inherited_effect'):
            translated['inherited_effect_jp'] = card['inherited_effect']
            translated['inherited_effect'] = self.translate_effect_text(card['inherited_effect'])
        
        if card.get('security_effect'):
            translated['security_effect_jp'] = card['security_effect']
            translated['security_effect'] = self.translate_effect_text(card['security_effect'])
        
        return translated
    
    def translate_cards_file(self, input_path: str, output_path: str) -> List[dict]:
        """翻译整个卡牌文件"""
        print(f"正在翻译: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        translated_cards = []
        total = len(cards)
        
        for i, card in enumerate(cards, 1):
            print(f"  翻译进度: {i}/{total} - {card.get('card_no', 'Unknown')}")
            translated = self.translate_card(card)
            translated_cards.append(translated)
        
        # 保存翻译结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translated_cards, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 翻译完成，已保存到: {output_path}")
        return translated_cards


    def translate_all_cards(self, input_dir: str, output_dir: str):
        """翻译目录下所有卡牌文件"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 查找所有卡牌JSON文件
        card_files = list(input_path.glob("*_cards.json"))
        print(f"找到 {len(card_files)} 个卡牌文件")
        
        for card_file in card_files:
            output_file = output_path / f"{card_file.stem}_cn.json"
            self.translate_cards_file(str(card_file), str(output_file))


def main():
    """主函数 - 翻译所有卡牌数据"""
    # 配置路径
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "digimon_card_data"
    output_dir = base_dir / "digimon_data" / "translated_cards"
    name_mapping_path = base_dir / "digimon_data" / "digimon_name_mapping.json"
    
    # 创建翻译器
    translator = CardTranslator(
        name_mapping_path=str(name_mapping_path) if name_mapping_path.exists() else None,
        use_ai=True,
        ai_provider="gemini"  # 或 "openai"
    )
    
    # 翻译所有卡牌
    translator.translate_all_cards(str(input_dir), str(output_dir))
    
    print("\n" + "=" * 60)
    print("翻译完成！")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
