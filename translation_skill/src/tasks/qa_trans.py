"""
QA 翻译任务
QA Translation Task
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

from ..translator import Translator
from ..utils.terminology import TerminologyManager, load_terminology_from_project
from ..config.translation_config import TranslationConfig


class QATranslator:
    """QA 翻译器"""
    
    def __init__(self,
                 terminology_path: Optional[str] = None,
                 card_data_path: Optional[str] = None,
                 input_qa_path: Optional[str] = None,
                 output_qa_path: Optional[str] = None,
                 engine_type: str = "qwen"):
        """
        初始化 QA 翻译器
        
        Args:
            terminology_path: 术语表 JSON 路径
            card_data_path: 中文卡牌数据 JSON 路径
            input_qa_path: 输入的日文 QA JSON 路径
            output_qa_path: 输出的中文 QA JSON 路径
            engine_type: 使用的翻译引擎 ('openai', 'gemini', 'qwen')
        """
        self.engine_type = engine_type
        
        # 设置默认路径
        project_root = TranslationConfig.PROJECT_ROOT
        
        self.terminology_path = Path(terminology_path) if terminology_path else \
            project_root / "digimon_card_data" / "term_mapping" / "llm_keywords_cn_jp.json"
        self.card_data_path = Path(card_data_path) if card_data_path else \
            project_root / "digimon_card_data" / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        self.input_qa_path = Path(input_qa_path) if input_qa_path else \
            project_root / "card_game_judge" / "card_game_QA_manger" / "official_qa_jp.json"
        self.output_qa_path = Path(output_qa_path) if output_qa_path else \
            TranslationConfig.get_output_path("rulings")
        
        # 初始化组件
        self.translator = Translator(default_engine=engine_type)
        self.terminology_manager = TerminologyManager()
        
        # 加载数据
        self.terminology: Dict[str, str] = {}
        self.card_mapping: Dict[str, Dict[str, str]] = {}
        self.translation_prompt = ""
        
        # 翻译状态
        self.checkpoint_file: Optional[Path] = None
    
    def load_data(self) -> Dict[str, int]:
        """
        加载术语表和卡牌数据
        
        Returns:
            加载统计信息
        """
        stats = {}
        
        # 加载术语表
        print("加载术语表...")
        if self.terminology_path.exists():
            self.terminology_manager = load_terminology_from_project(TranslationConfig.PROJECT_ROOT)
            self.terminology = self.terminology_manager.terminology
            stats['terminology_count'] = len(self.terminology)
            print(f"✓ 加载了 {stats['terminology_count']} 个术语")
        else:
            print(f"⚠ 术语表不存在：{self.terminology_path}")
            stats['terminology_count'] = 0
        
        # 加载卡牌数据
        print("\n加载卡牌数据...")
        if self.card_data_path.exists():
            with open(self.card_data_path, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            
            # 按卡号建立索引
            self.card_mapping = {}
            for card in cards:
                card_no = card.get('card_no', '')
                if card_no:
                    self.card_mapping[card_no] = {
                        'name_cn': card.get('name_cn', ''),
                        'name_jp': card.get('name_jp', ''),
                        'card_no': card_no
                    }
            
            stats['card_count'] = len(self.card_mapping)
            print(f"✓ 加载了 {stats['card_count']} 张卡牌数据")
        else:
            print(f"⚠ 卡牌数据不存在：{self.card_data_path}")
            stats['card_count'] = 0
        
        # 构建翻译提示词
        self._build_translation_prompt()
        
        return stats
    
    def _build_translation_prompt(self) -> str:
        """构建翻译提示词"""
        # 构建术语表文本（限制数量以避免 token 超限）
        term_examples = []
        count = 0
        for jp, cn_list in self.terminology.items():
            if count >= 100:
                break
            cn = cn_list if isinstance(cn_list, str) else (cn_list[0] if cn_list else "")
            term_examples.append(f"  {jp} → {cn}")
            count += 1
        
        terms_text = "\n".join(term_examples)
        if len(self.terminology) > 100:
            terms_text += f"\n  ... (共{len(self.terminology)}个术语)"
        
        prompt = f"""你是一位专业的数码宝贝卡牌游戏翻译专家。你的任务是将日文 QA 完整翻译成中文。

## 核心要求（必须严格遵守）

1. **完全翻译**: 必须将所有日文翻译成中文汉字，不得保留任何日文假名或汉字
2. **术语对照**: 严格按照下方术语对照表翻译，不得自创译名
3. **自然流畅**: 翻译后的中文要符合中文语法习惯，读起来自然流畅

## 专有名词对照表（必须 100% 遵守）

{terms_text}

## 详细翻译规则

### 1. 效果标记
- 【登場時】→【登场时】
- 【進化時】→【进化时】
- 【アタック時】→【攻击时】
- 【安防】→【安防】
- 必须使用中文方括号【】

### 2. 游戏术语（必须使用对照表）
- デジモン → 数码兽
- レスト → 休眠
- アクティブ → 活跃
- 進化 → 进化
- 登場 → 登场
- アタック → 攻击
- バトルエリア → 战斗区
- 育成エリア → 培育区
- トラッシュ → 废弃区
- セキュリティ → 安防
- デッキ → 卡组
- 手札 → 手牌
- 破棄 → 弃置
- 消滅 → 消灭

### 3. 常见表达
- できますか？→ 可以吗？
- できません → 不可以
- はい → 是的
- いいえ → 不是
- 場合 → 情况
- 時 → 时
- 効果 → 效果
- 発揮 → 发挥
- 選ぶ → 选择
- 持つ → 持有
- 存在する → 存在

### 4. 数值和符号
- DP、Lv.、+、- 等保持原样
- 数字保持原样

### 5. 日期格式
- 保持不变（如：2026/01/30 更新）

## 翻译示例

### 示例 1
**日文**: このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
**中文**: 这张卡的【登场时】【进化时】效果，可以休眠自己或对手的任意数码兽吗？

### 示例 2
**日文**: はい、レストできます。
**中文**: 是的，可以休眠。

### 示例 3
**日文**: バトルエリアにレスト状態の自分のこのカードが存在する場合、相手のデジモンはアタックできますか？
**中文**: 当战斗区存在休眠状态的自己的这张卡时，对手的数码兽可以攻击吗？

## 重要提醒

❌ 错误示例（保留了日文）:
- "此卡牌の【登场时】効果は..." 
- "はい、休眠できます"
- "对手の数码宝贝を选择ことはできず"

✅ 正确示例（完全中文）:
- "这张卡的【登场时】效果..."
- "是的，可以休眠"
- "无法选择对手的数码兽"

## 翻译任务

请将以下日文完整翻译成中文，不要保留任何日文："""
        
        self.translation_prompt = prompt
        return prompt
    
    def _get_card_context(self, card_no: Optional[str]) -> str:
        """获取卡牌上下文信息"""
        if not card_no or card_no not in self.card_mapping:
            return ""
        
        card_info = self.card_mapping[card_no]
        return f"\n\n【卡牌信息】\n卡号：{card_no}\n日文名：{card_info['name_jp']}\n中文名：{card_info['name_cn']}"
    
    def translate_text(self, text: str, card_no: Optional[str] = None) -> str:
        """
        使用 LLM 翻译文本
        
        Args:
            text: 待翻译的文本
            card_no: 卡号（可选）
        
        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text
        
        # 构建完整提示
        card_context = self._get_card_context(card_no)
        full_prompt = f"{self.translation_prompt}{card_context}\n\n---\n\n{text}"
        
        try:
            result = self.translator.translate(full_prompt, engine=self.engine_type)
            return result.strip()
        except Exception as e:
            print(f"  翻译失败：{e}")
            return text
    
    def translate_qa_item(self, qa_item: Dict) -> Dict:
        """
        翻译单个 QA 条目
        
        Args:
            qa_item: QA 条目字典
        
        Returns:
            翻译后的 QA 条目
        """
        translated = qa_item.copy()
        card_no = qa_item.get('card_no', '')
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
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
                if card_no and card_no in self.card_mapping:
                    card_info = self.card_mapping[card_no]
                    translated['card_name'] = f"{card_no} {card_info['name_cn']}"
                    if 'card_name' in qa_item:
                        translated['card_name_original'] = qa_item['card_name']
                
                # 更新元数据
                translated['language'] = 'zh-cn'
                translated['translated_from'] = 'ja'
                translated['translation_method'] = f'llm_{self.engine_type}'
                
                return translated
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    print(f"\n  ❌ QA 翻译失败：{e}")
                    translated['translation_error'] = str(e)
                    return translated
        
        return translated
    
    def translate_all(self, batch_size: int = 10, delay: float = 1.0,
                     start_from: int = 0, max_count: Optional[int] = None) -> Dict:
        """
        翻译所有 QA 条目
        
        Args:
            batch_size: 每批处理的数量
            delay: 每批之间的延迟（秒）
            start_from: 从第几条开始（用于断点续传）
            max_count: 最多翻译多少条（None 表示全部）
        
        Returns:
            翻译统计信息
        """
        stats = {
            'total': 0,
            'translated': 0,
            'errors': 0,
            'start_from': start_from,
            'engine': self.engine_type
        }
        
        # 加载日文 QA
        print(f"\n正在加载日文 QA: {self.input_qa_path}")
        if not self.input_qa_path.exists():
            raise FileNotFoundError(f"输入文件不存在：{self.input_qa_path}")
        
        with open(self.input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        stats['total'] = len(qa_list)
        print(f"✓ 加载了 {stats['total']} 条 QA")
        
        # 加载检查点（如果存在）
        translated_list = []
        self.checkpoint_file = self.output_qa_path.parent / f"{self.output_qa_path.stem}_checkpoint.json"
        
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                translated_list = checkpoint.get('translated', [])
                last_index = checkpoint.get('last_index', -1)
                
                if last_index >= len(qa_list) - 1:
                    print(f"✓ 检查点显示已完成所有翻译")
                    self._save_final(translated_list)
                    self.checkpoint_file.unlink()
                    stats['translated'] = len(translated_list)
                    return stats
                
                start_from = last_index + 1
                print(f"✓ 从检查点恢复：已翻译 {len(translated_list)} 条，从第 {start_from + 1} 条继续")
        
        # 确定翻译范围
        end_at = len(qa_list) if max_count is None else min(start_from + max_count, len(qa_list))
        
        if start_from >= len(qa_list):
            print(f"⚠️ 起始位置 {start_from + 1} 超出范围（总共 {len(qa_list)} 条）")
            self._save_final(translated_list)
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            stats['translated'] = len(translated_list)
            return stats
        
        to_translate = qa_list[start_from:end_at]
        
        print(f"\n开始翻译 (从第 {start_from+1} 条到第 {end_at} 条)...")
        print(f"使用引擎：{self.engine_type}")
        print(f"预计时间：{len(to_translate) * delay / 60:.1f} 分钟\n")
        
        # 翻译
        for i, qa_item in enumerate(to_translate, start_from):
            try:
                print(f"[{i+1}/{end_at}] ", end='', flush=True)
                
                translated = self.translate_qa_item(qa_item)
                translated_list.append(translated)
                stats['translated'] += 1
                
                print("✓")
                
                # 定期保存检查点
                if (i + 1) % batch_size == 0:
                    self._save_checkpoint(translated_list, i)
                    if i + 1 < end_at:
                        time.sleep(delay)
                
            except KeyboardInterrupt:
                print(f"\n\n用户中断！已保存进度到第 {i} 条")
                self._save_checkpoint(translated_list, i)
                stats['errors'] += 1
                return stats
            except Exception as e:
                print(f"✗ 错误：{e}")
                translated_list.append(qa_item)
                stats['errors'] += 1
                self._save_checkpoint(translated_list, i)
        
        # 最终保存
        self._save_final(translated_list)
        
        # 删除检查点
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        
        print(f"\n{'=' * 60}")
        print(f"✅ 翻译完成！")
        print(f"输出文件：{self.output_qa_path}")
        print(f"翻译数量：{stats['translated']}/{stats['total']}")
        print(f"错误数量：{stats['errors']}")
        print(f"{'=' * 60}")
        
        return stats
    
    def _save_checkpoint(self, translated_list: List[Dict], last_index: int):
        """保存检查点"""
        if not self.checkpoint_file:
            return
        
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            'last_index': last_index,
            'total': len(translated_list),
            'translated': translated_list
        }
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def _save_final(self, translated_list: List[Dict]):
        """保存最终结果"""
        self.output_qa_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_qa_path, 'w', encoding='utf-8') as f:
            json.dump(translated_list, f, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    import sys
    
    print("DTCG QA 翻译工具")
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
    print("  1. 测试模式 (翻译前 10 条)")
    print("  2. 小批量 (翻译前 100 条)")
    print("  3. 完整翻译 (翻译全部)")
    
    mode = input("\n请选择模式 (1/2/3，默认 1): ").strip() or "1"
    
    # 创建翻译器
    translator = QATranslator(engine_type=engine)
    translator.load_data()
    
    # 执行翻译
    try:
        if mode == '1':
            stats = translator.translate_all(batch_size=5, delay=1.0, max_count=10)
        elif mode == '2':
            stats = translator.translate_all(batch_size=10, delay=1.0, max_count=100)
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
        
        print(f"\n✓ 翻译完成！输出：{translator.output_qa_path}")
    except Exception as e:
        print(f"\n❌ 翻译失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
