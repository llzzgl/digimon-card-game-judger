"""
使用大语言模型进行高质量日文QA翻译
确保翻译信达雅，通俗易懂，同时保持专有名词准确
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 尝试导入Google Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("警告: google-generativeai未安装")
    print("安装方法: pip install google-generativeai")


class LLMQATranslator:
    def __init__(self, 
                 terminology_path: str,
                 card_data_path: str,
                 input_qa_path: str,
                 output_qa_path: str,
                 api_key: Optional[str] = None):
        """
        初始化LLM翻译器
        
        Args:
            terminology_path: 术语表JSON路径
            card_data_path: 中文卡牌数据JSON路径
            input_qa_path: 输入的日文QA JSON路径
            output_qa_path: 输出的中文QA JSON路径
            api_key: Gemini API密钥（可选，从环境变量读取）
        """
        self.terminology_path = Path(terminology_path)
        self.card_data_path = Path(card_data_path)
        self.input_qa_path = Path(input_qa_path)
        self.output_qa_path = Path(output_qa_path)
        
        # 加载数据
        self.terminology = self._load_terminology()
        self.card_mapping = self._load_card_mapping()
        
        # 初始化LLM
        if not api_key:
            load_dotenv()
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("请设置GEMINI_API_KEY或GOOGLE_API_KEY环境变量或传入api_key参数")
        
        if not HAS_GEMINI:
            raise ImportError("请安装google-generativeai: pip install google-generativeai")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 构建翻译提示词
        self.translation_prompt = self._build_translation_prompt()
    
    def _load_terminology(self) -> Dict[str, str]:
        """加载术语表"""
        with open(self.terminology_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        term_map = {}
        for category, terms in data.items():
            if isinstance(terms, dict):
                term_map.update(terms)
        
        print(f"✓ 加载了 {len(term_map)} 个术语")
        return term_map
    
    def _load_card_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载卡牌数据"""
        with open(self.card_data_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
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
    
    def _build_translation_prompt(self) -> str:
        """构建翻译提示词"""
        # 提取常用术语
        common_terms = []
        for jp, cn in list(self.terminology.items())[:50]:
            common_terms.append(f"  - {jp} → {cn}")
        
        terms_text = "\n".join(common_terms)
        
        prompt = f"""你是一位专业的数码宝贝卡牌游戏翻译专家。你的任务是将日文QA翻译成高质量的中文，要求：

## 翻译原则

1. **信达雅**: 准确传达原意，表达流畅自然，符合中文习惯
2. **通俗易懂**: 使用简洁明了的语言，避免生硬的直译
3. **专业准确**: 游戏专有名词必须使用标准译名

## 专有名词对照表（必须严格遵守）

{terms_text}

## 翻译要求

1. **效果标记**: 【登場時】→【登场时】、【進化時】→【进化时】等，必须使用中文方括号
2. **卡牌名称**: 如果提供了卡号和中文卡名，必须使用中文卡名
3. **语气**: 问句保持疑问语气，答句保持陈述语气
4. **数值**: DP、Lv.等保持原样
5. **流畅度**: 翻译后的句子要符合中文语法，读起来自然流畅

## 示例

**日文**: このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
**中文**: 这张卡的【登场时】【进化时】效果，可以休眠自己或对手的任意数码宝贝吗？

**日文**: はい、レストできます。
**中文**: 是的，可以休眠。

## 注意事项

- 不要逐字翻译，要理解句意后用自然的中文表达
- 保持原文的完整性，不要遗漏信息
- 日期格式保持不变（如：2026/01/30 更新）
- 如果有不确定的术语，保持原文

请按照以上要求翻译以下内容。"""
        
        return prompt
    
    def _get_card_context(self, card_no: Optional[str]) -> str:
        """获取卡牌上下文信息"""
        if not card_no or card_no not in self.card_mapping:
            return ""
        
        card_info = self.card_mapping[card_no]
        return f"\n\n卡牌信息：\n- 卡号: {card_no}\n- 日文名: {card_info['name_jp']}\n- 中文名: {card_info['name_cn']}"
    
    def translate_text(self, text: str, card_no: Optional[str] = None) -> str:
        """使用LLM翻译文本"""
        if not text:
            return text
        
        # 构建完整提示
        card_context = self._get_card_context(card_no)
        full_prompt = f"{self.translation_prompt}{card_context}\n\n---\n\n{text}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"翻译失败: {e}")
            return text
    
    def translate_qa_item(self, qa_item: Dict) -> Dict:
        """翻译单个QA条目"""
        translated = qa_item.copy()
        card_no = qa_item.get('card_no', '')
        
        # 翻译问题
        question = qa_item.get('question', '')
        if question:
            translated_question = self.translate_text(question, card_no)
            translated['question'] = translated_question
            translated['question_original'] = question
        
        # 翻译答案
        answer = qa_item.get('answer', '')
        if answer:
            translated_answer = self.translate_text(answer, card_no)
            translated['answer'] = translated_answer
            translated['answer_original'] = answer
        
        # 更新卡牌名称
        if 'card_name' in qa_item and card_no and card_no in self.card_mapping:
            card_info = self.card_mapping[card_no]
            translated['card_name'] = f"{card_no} {card_info['name_cn']}"
            translated['card_name_original'] = qa_item.get('card_name', '')
        
        # 更新元数据
        translated['language'] = 'zh-cn'
        translated['translated_from'] = 'ja'
        translated['translation_method'] = 'llm_gemini'
        
        return translated
    
    def translate_all(self, batch_size: int = 5, delay: float = 2.0, 
                     start_from: int = 0, max_count: Optional[int] = None):
        """
        翻译所有QA条目
        
        Args:
            batch_size: 每批处理的数量
            delay: 每批之间的延迟（秒）
            start_from: 从第几条开始（用于断点续传）
            max_count: 最多翻译多少条（None表示全部）
        """
        # 加载日文QA
        print(f"\n正在加载日文QA: {self.input_qa_path}")
        with open(self.input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        print(f"✓ 加载了 {len(qa_list)} 条QA")
        
        # 加载已翻译的数据（如果存在）
        translated_list = []
        if self.output_qa_path.exists() and start_from > 0:
            with open(self.output_qa_path, 'r', encoding='utf-8') as f:
                translated_list = json.load(f)
            print(f"✓ 加载了 {len(translated_list)} 条已翻译的QA")
        
        # 确定翻译范围
        end_at = len(qa_list) if max_count is None else min(start_from + max_count, len(qa_list))
        to_translate = qa_list[start_from:end_at]
        
        print(f"\n开始翻译 (从第 {start_from+1} 条到第 {end_at} 条)...")
        print(f"预计时间: {len(to_translate) * delay / 60:.1f} 分钟")
        
        # 翻译
        for i, qa_item in enumerate(to_translate, start_from+1):
            try:
                print(f"\n[{i}/{end_at}] 翻译中...", end='')
                
                translated = self.translate_qa_item(qa_item)
                translated_list.append(translated)
                
                print(f" ✓")
                
                # 显示翻译结果
                if i % 10 == 0:
                    print(f"\n示例 - QA #{qa_item.get('qa_number', 'N/A')}:")
                    print(f"原文: {qa_item.get('question', '')[:60]}...")
                    print(f"译文: {translated.get('question', '')[:60]}...")
                
                # 定期保存
                if i % batch_size == 0:
                    self._save_progress(translated_list)
                    if i < end_at:
                        print(f"\n等待 {delay} 秒...")
                        time.sleep(delay)
                    
            except Exception as e:
                print(f" ✗ 错误: {e}")
                # 保留原始数据
                translated_list.append(qa_item)
        
        # 最终保存
        self._save_progress(translated_list)
        
        print(f"\n✓ 翻译完成！共翻译 {len(translated_list)} 条QA")
        print(f"✓ 输出文件: {self.output_qa_path}")
    
    def _save_progress(self, translated_list: List[Dict]):
        """保存翻译进度"""
        self.output_qa_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_qa_path, 'w', encoding='utf-8') as f:
            json.dump(translated_list, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    
    terminology_path = base_dir / "digimon_data" / "dtcg_terminology.json"
    card_data_path = base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
    input_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_jp.json"
    output_qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_cn_llm.json"
    
    print("="*60)
    print("高质量LLM翻译工具")
    print("="*60)
    print("\n使用Gemini 2.0 Flash进行翻译")
    print("确保翻译信达雅，通俗易懂\n")
    
    # 创建翻译器
    try:
        translator = LLMQATranslator(
            terminology_path=str(terminology_path),
            card_data_path=str(card_data_path),
            input_qa_path=str(input_qa_path),
            output_qa_path=str(output_qa_path)
        )
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n请确保:")
        print("1. 已安装 google-generativeai: pip install google-generativeai")
        print("2. 已设置环境变量 GEMINI_API_KEY")
        print("3. 或在 .env 文件中配置 GEMINI_API_KEY")
        return
    
    # 询问翻译模式
    print("\n翻译模式:")
    print("1. 测试模式 (翻译前10条)")
    print("2. 完整翻译 (翻译全部4634条)")
    print("3. 断点续传 (从指定位置继续)")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == '1':
        # 测试模式
        translator.translate_all(batch_size=5, delay=2.0, start_from=0, max_count=10)
    elif choice == '2':
        # 完整翻译
        confirm = input("\n完整翻译需要约2-3小时，确认继续? (y/n): ").strip().lower()
        if confirm == 'y':
            translator.translate_all(batch_size=5, delay=2.0)
        else:
            print("已取消")
    elif choice == '3':
        # 断点续传
        start = int(input("从第几条开始? "))
        translator.translate_all(batch_size=5, delay=2.0, start_from=start)
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
