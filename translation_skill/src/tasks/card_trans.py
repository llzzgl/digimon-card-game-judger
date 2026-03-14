"""
卡牌翻译任务
Card Translation Task
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import time

from ..translator import Translator
from ..utils.terminology import TerminologyManager, load_terminology_from_project
from ..config.translation_config import TranslationConfig


class CardTranslator:
    """卡牌翻译器"""
    
    def __init__(self,
                 input_card_path: Optional[str] = None,
                 output_card_path: Optional[str] = None,
                 engine_type: str = "qwen"):
        """
        初始化卡牌翻译器
        
        Args:
            input_card_path: 输入的日文卡牌数据 JSON 路径
            output_card_path: 输出的中文卡牌数据 JSON 路径
            engine_type: 使用的翻译引擎
        """
        self.engine_type = engine_type
        
        # 设置默认路径
        project_root = TranslationConfig.PROJECT_ROOT
        
        self.input_card_path = Path(input_card_path) if input_card_path else \
            project_root / "digimon_card_data" / "digimon_cards_jp.json"
        self.output_card_path = Path(output_card_path) if output_card_path else \
            project_root / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        # 初始化组件
        self.translator = Translator(default_engine=engine_type)
        self.terminology_manager = TerminologyManager()
        
        # 加载数据
        self.terminology: Dict[str, str] = {}
        self.translation_prompt = ""
    
    def load_data(self) -> Dict[str, int]:
        """
        加载术语表
        
        Returns:
            加载统计信息
        """
        stats = {}
        
        # 加载术语表
        print("加载术语表...")
        self.terminology_manager = load_terminology_from_project(TranslationConfig.PROJECT_ROOT)
        self.terminology = self.terminology_manager.terminology
        stats['terminology_count'] = len(self.terminology)
        print(f"✓ 加载了 {stats['terminology_count']} 个术语")
        
        # 构建翻译提示词
        self._build_translation_prompt()
        
        return stats
    
    def _build_translation_prompt(self) -> str:
        """构建卡牌翻译提示词"""
        # 构建术语表文本
        term_examples = []
        count = 0
        for jp, cn_list in self.terminology.items():
            if count >= 50:
                break
            cn = cn_list if isinstance(cn_list, str) else (cn_list[0] if cn_list else "")
            term_examples.append(f"  {jp} → {cn}")
            count += 1
        
        terms_text = "\n".join(term_examples)
        if len(self.terminology) > 50:
            terms_text += f"\n  ... (共{len(self.terminology)}个术语)"
        
        prompt = f"""你是一位专业的数码宝贝卡牌游戏翻译专家。你的任务是将日文卡牌数据翻译成中文。

## 核心要求

1. **完全翻译**: 将所有日文翻译成中文
2. **术语对照**: 使用下方术语对照表
3. **保持格式**: JSON 结构保持不变，只翻译文本字段
4. **保留数据**: 卡号、数值、符号等保持不变

## 术语对照表（部分）

{terms_text}

## 需要翻译的字段

- name_jp → name_cn (卡牌名称)
- effect_jp → effect_cn (效果文本)
- flavor_text_jp → flavor_text_cn ( flavor 文本)
- evolution_source_jp → evolution_source_cn (进化源)
- 其他日文文本字段

## 不需要翻译的字段

- card_no (卡号)
- dp (数值)
- level (等级)
- cost (费用)
- attribute (属性代码)
- type (类型代码)
- rarity (稀有度代码)
- image_url (图片链接)

## 翻译示例

**日文卡牌**:
{{
  "card_no": "BT1-001",
  "name_jp": "アグモン",
  "effect_jp": "このデジモンは攻撃できない。",
  "dp": 1000,
  "level": 3
}}

**中文卡牌**:
{{
  "card_no": "BT1-001",
  "name_cn": "亚古兽",
  "effect_cn": "这只数码兽不能攻击。",
  "dp": 1000,
  "level": 3
}}

## 翻译任务

请将以下日文卡牌数据翻译成中文："""
        
        self.translation_prompt = prompt
        return prompt
    
    def translate_card(self, card: Dict) -> Dict:
        """
        翻译单张卡牌
        
        Args:
            card: 卡牌数据字典
        
        Returns:
            翻译后的卡牌数据
        """
        translated = card.copy()
        
        # 构建待翻译的文本
        text_to_translate = {}
        
        if 'name_jp' in card and card['name_jp']:
            text_to_translate['name_jp'] = card['name_jp']
        
        if 'effect_jp' in card and card['effect_jp']:
            text_to_translate['effect_jp'] = card['effect_jp']
        
        if 'flavor_text_jp' in card and card['flavor_text_jp']:
            text_to_translate['flavor_text_jp'] = card['flavor_text_jp']
        
        if 'evolution_source_jp' in card and card['evolution_source_jp']:
            text_to_translate['evolution_source_jp'] = card['evolution_source_jp']
        
        if not text_to_translate:
            # 没有需要翻译的内容
            return translated
        
        # 构建翻译请求
        context = {
            "terminology": self.terminology,
            "card_info": {
                "card_no": card.get('card_no', ''),
                "name_jp": card.get('name_jp', '')
            }
        }
        
        try:
            # 翻译所有文本字段
            for field, text in text_to_translate.items():
                cn_field = field.replace('_jp', '_cn')
                
                print(f" [{field}]", end='', flush=True)
                
                translated_text = self.translator.translate(
                    text,
                    engine=self.engine_type,
                    context=context
                )
                
                translated[cn_field] = translated_text
            
            # 标记为已翻译
            translated['translated'] = True
            translated['translation_method'] = f'llm_{self.engine_type}'
            
        except Exception as e:
            print(f" [错误：{e}]", end='', flush=True)
            translated['translation_error'] = str(e)
            translated['translated'] = False
        
        return translated
    
    def translate_all(self, batch_size: int = 10, delay: float = 1.0,
                     start_from: int = 0, max_count: Optional[int] = None) -> Dict:
        """
        翻译所有卡牌
        
        Args:
            batch_size: 每批处理的数量
            delay: 每批之间的延迟（秒）
            start_from: 从第几张开始
            max_count: 最多翻译多少张
        
        Returns:
            翻译统计信息
        """
        stats = {
            'total': 0,
            'translated': 0,
            'errors': 0,
            'engine': self.engine_type
        }
        
        # 加载日文卡牌数据
        print(f"\n正在加载日文卡牌：{self.input_card_path}")
        if not self.input_card_path.exists():
            raise FileNotFoundError(f"输入文件不存在：{self.input_card_path}")
        
        with open(self.input_card_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        stats['total'] = len(cards)
        print(f"✓ 加载了 {stats['total']} 张卡牌")
        
        # 确定翻译范围
        end_at = len(cards) if max_count is None else min(start_from + max_count, len(cards))
        to_translate = cards[start_from:end_at]
        
        print(f"\n开始翻译 (从第 {start_from+1} 张到第 {end_at} 张)...")
        print(f"使用引擎：{self.engine_type}\n")
        
        # 翻译
        translated_cards = []
        
        for i, card in enumerate(to_translate, start_from):
            try:
                print(f"[{i+1}/{end_at}] {card.get('card_no', 'N/A')}", end='', flush=True)
                
                translated = self.translate_card(card)
                translated_cards.append(translated)
                stats['translated'] += 1
                
                print(" ✓")
                
                # 批次延迟
                if (i + 1) % batch_size == 0 and i + 1 < end_at:
                    time.sleep(delay)
                
            except KeyboardInterrupt:
                print(f"\n\n用户中断！已翻译 {len(translated_cards)} 张")
                self._save_result(translated_cards)
                stats['errors'] += 1
                return stats
            except Exception as e:
                print(f" ✗ 错误：{e}")
                translated_cards.append(card)
                stats['errors'] += 1
        
        # 保存结果
        self._save_result(translated_cards)
        
        print(f"\n{'=' * 60}")
        print(f"✅ 翻译完成！")
        print(f"输出文件：{self.output_card_path}")
        print(f"翻译数量：{stats['translated']}/{stats['total']}")
        print(f"错误数量：{stats['errors']}")
        print(f"{'=' * 60}")
        
        return stats
    
    def _save_result(self, translated_cards: List[Dict]):
        """保存翻译结果"""
        self.output_card_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_card_path, 'w', encoding='utf-8') as f:
            json.dump(translated_cards, f, ensure_ascii=False, indent=2)
        print(f"✓ 结果已保存：{self.output_card_path}")


def main():
    """命令行入口"""
    print("DTCG 卡牌翻译工具")
    print("=" * 60)
    
    # 选择引擎
    print("\n支持的引擎:")
    print("  1. qwen    - 通义千问 (推荐)")
    print("  2. openai  - OpenAI")
    print("  3. gemini  - Google Gemini")
    
    choice = input("\n请选择引擎 (1/2/3，默认 1): ").strip() or "1"
    engine_map = {"1": "qwen", "2": "openai", "3": "gemini"}
    engine = engine_map.get(choice, "qwen")
    
    print(f"\n使用引擎：{engine}")
    
    # 选择模式
    print("\n翻译模式:")
    print("  1. 测试模式 (翻译前 5 张)")
    print("  2. 小批量 (翻译前 50 张)")
    print("  3. 完整翻译 (翻译全部)")
    
    mode = input("\n请选择模式 (1/2/3，默认 1): ").strip() or "1"
    
    # 创建翻译器
    translator = CardTranslator(engine_type=engine)
    translator.load_data()
    
    # 执行翻译
    try:
        if mode == '1':
            stats = translator.translate_all(batch_size=5, delay=1.0, max_count=5)
        elif mode == '2':
            stats = translator.translate_all(batch_size=10, delay=1.0, max_count=50)
        elif mode == '3':
            confirm = input("\n完整翻译需要较长时间，确认继续？(y/n): ").strip().lower()
            if confirm == 'y':
                stats = translator.translate_all(batch_size=10, delay=1.0)
            else:
                print("已取消")
                return
        else:
            print("无效选择")
            return
        
        print(f"\n✓ 翻译完成！输出：{translator.output_card_path}")
    except Exception as e:
        print(f"\n❌ 翻译失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
