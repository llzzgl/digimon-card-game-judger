"""
使用大语言模型和专有名词表进行高质量日文QA翻译
支持: Qwen (通义千问)、Gemini、Ollama
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv


class MultiLLMQATranslator:
    def __init__(self, 
                 llm_type: str = "qwen",
                 terminology_path: Optional[str] = None,
                 card_data_path: Optional[str] = None,
                 input_qa_path: Optional[str] = None,
                 output_qa_path: Optional[str] = None):
        """
        初始化多LLM翻译器
        
        Args:
            llm_type: LLM类型 ("qwen", "gemini", "ollama")
            terminology_path: 术语表JSON路径
            card_data_path: 中文卡牌数据JSON路径
            input_qa_path: 输入的日文QA JSON路径
            output_qa_path: 输出的中文QA JSON路径
        """
        self.llm_type = llm_type
        
        # Qwen模型列表（按优先级排序）
        self.qwen_models = [
            "qwen-turbo",      # 快速、便宜
            "qwen-plus",       # 平衡
            "qwen-max",        # 高质量
            "qwen-long",       # 长文本
        ]
        self.current_model_index = 0  # 当前使用的模型索引
        
        # 设置默认路径
        base_dir = Path(__file__).parent.parent.parent
        self.terminology_path = Path(terminology_path) if terminology_path else \
            base_dir / "digimon_card_data" / "term_mapping" / "game_mechanics_keywords.json"
        self.card_data_path = Path(card_data_path) if card_data_path else \
            base_dir / "digimon_card_data" / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        self.input_qa_path = Path(input_qa_path) if input_qa_path else \
            Path(__file__).parent / "official_qa_jp.json"
        self.output_qa_path = Path(output_qa_path) if output_qa_path else \
            Path(__file__).parent / f"official_qa_cn_{llm_type}.json"
        
        # 加载环境变量
        env_path = base_dir / "card_game_judge" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # 加载数据
        print("加载数据...")
        self.terminology = self._load_terminology()
        self.card_mapping = self._load_card_mapping()
        
        # 初始化LLM客户端
        print(f"初始化 {llm_type} 客户端...")
        self._init_llm_client()
        
        # 构建翻译提示词
        self.translation_prompt = self._build_translation_prompt()
        
        print("✓ 初始化完成")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if self.llm_type == "qwen":
            self._init_qwen()
        elif self.llm_type == "gemini":
            self._init_gemini()
        elif self.llm_type == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"不支持的LLM类型: {self.llm_type}")
    
    def _init_qwen(self):
        """初始化通义千问"""
        from openai import OpenAI
        
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        # 使用模型列表中的第一个模型
        self.model_name = self.qwen_models[self.current_model_index]
        print(f"✓ 通义千问已初始化 (模型: {self.model_name})")
        print(f"  可用模型列表: {', '.join(self.qwen_models)}")
    
    def _switch_to_next_qwen_model(self):
        """切换到下一个Qwen模型"""
        self.current_model_index += 1
        if self.current_model_index >= len(self.qwen_models):
            print("\n❌ 所有Qwen模型都已用尽配额！")
            return False
        
        self.model_name = self.qwen_models[self.current_model_index]
        print(f"\n⚠️ 切换到模型: {self.model_name}")
        return True
    
    def _init_gemini(self):
        """初始化Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("请安装google-generativeai: pip install google-generativeai")
        
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("请设置GEMINI_API_KEY或GOOGLE_API_KEY环境变量")
        
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Gemini已初始化")
    
    def _init_ollama(self):
        """初始化Ollama"""
        from openai import OpenAI
        
        # Ollama使用OpenAI兼容接口
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Ollama不需要真实的API key
        )
        self.model_name = "qwen2:7b"  # 或其他本地模型
        print(f"✓ Ollama已初始化 (模型: {self.model_name})")
    
    def _call_llm(self, prompt: str) -> str:
        """统一的LLM调用接口"""
        if self.llm_type == "qwen":
            return self._call_qwen(prompt)
        elif self.llm_type == "gemini":
            return self._call_gemini(prompt)
        elif self.llm_type == "ollama":
            return self._call_ollama(prompt)
    
    def _call_qwen(self, prompt: str) -> str:
        """调用通义千问"""
        max_retries = 3  # 每个模型最多重试3次
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f" [重试{attempt}]", end='', flush=True)
                
                print("  调用Qwen API...", end='', flush=True)
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一位专业的数码宝贝卡牌游戏翻译专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=60  # 60秒超时
                )
                print(" 完成", flush=True)
                return response.choices[0].message.content
                
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额用尽错误
                if "AllocationQuota.FreeTierOnly" in error_str or "403" in error_str:
                    print(f" 配额用尽", flush=True)
                    print(f"  ⚠️ 模型 {self.model_name} 免费配额已用尽")
                    
                    # 尝试切换到下一个模型
                    if self._switch_to_next_qwen_model():
                        print(f"  ↻ 使用新模型重试...")
                        # 不增加attempt计数，直接用新模型重试
                        continue
                    else:
                        # 所有模型都用尽了
                        raise Exception("所有Qwen模型配额都已用尽，请升级到付费版本或稍后再试")
                
                # 其他错误
                print(f" 失败: {e}", flush=True)
                
                if attempt == max_retries - 1:
                    # 最后一次重试也失败了
                    raise
                
                # 等待后重试
                import time
                time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s
        
        raise Exception("翻译失败，已达到最大重试次数")
    
    def _call_gemini(self, prompt: str) -> str:
        """调用Gemini"""
        response = self.client.generate_content(prompt)
        return response.text
    
    def _call_ollama(self, prompt: str) -> str:
        """调用Ollama"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一位专业的数码宝贝卡牌游戏翻译专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _load_terminology(self) -> Dict[str, List[str]]:
        """加载术语表"""
        if not self.terminology_path.exists():
            print(f"警告: 术语表不存在: {self.terminology_path}")
            return {}
        
        with open(self.terminology_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ 加载了 {len(data)} 个术语")
        return data
    
    def _load_card_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载卡牌数据"""
        if not self.card_data_path.exists():
            print(f"警告: 卡牌数据不存在: {self.card_data_path}")
            return {}
        
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
        # 构建术语表文本
        term_examples = []
        count = 0
        for jp, cn_list in self.terminology.items():
            if count >= 100:  # 显示更多术语
                break
            cn = cn_list[0] if isinstance(cn_list, list) else cn_list
            term_examples.append(f"  {jp} → {cn}")
            count += 1
        
        terms_text = "\n".join(term_examples)
        if len(self.terminology) > 100:
            terms_text += f"\n  ... (共{len(self.terminology)}个术语)"
        
        prompt = f"""你是一位专业的数码宝贝卡牌游戏翻译专家。你的任务是将日文QA完整翻译成中文。

## 核心要求（必须严格遵守）

1. **完全翻译**: 必须将所有日文翻译成中文汉字，不得保留任何日文假名或汉字
2. **术语对照**: 严格按照下方术语对照表翻译，不得自创译名
3. **自然流畅**: 翻译后的中文要符合中文语法习惯，读起来自然流畅

## 专有名词对照表（必须100%遵守）

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

### 示例1
**日文**: このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
**中文**: 这张卡的【登场时】【进化时】效果，可以休眠自己或对手的任意数码兽吗？

### 示例2
**日文**: はい、レストできます。
**中文**: 是的，可以休眠。

### 示例3
**日文**: バトルエリアにレスト状態の自分のこのカードが存在する場合、相手のデジモンはアタックできますか？
**中文**: 当战斗区存在休眠状态的自己的这张卡时，对手的数码兽可以攻击吗？

### 示例4
**日文**: いいえ、アタックできません。「できる」効果と「できない」効果が同時にある場合は、「できない」効果が優先されます。
**中文**: 不是，不可以攻击。当"可以"效果和"不可以"效果同时存在时，"不可以"效果优先。

## 重要提醒

❌ 错误示例（保留了日文）:
- "此卡牌の【登场时】效果は..." 
- "はい、休眠できます"
- "对手の数码宝贝を选择ことはできず"

✅ 正确示例（完全中文）:
- "这张卡的【登场时】效果..."
- "是的，可以休眠"
- "无法选择对手的数码兽"

## 翻译任务

请将以下日文完整翻译成中文，不要保留任何日文："""
        
        return prompt
    
    def _get_card_context(self, card_no: Optional[str]) -> str:
        """获取卡牌上下文信息"""
        if not card_no or card_no not in self.card_mapping:
            return ""
        
        card_info = self.card_mapping[card_no]
        return f"\n\n【卡牌信息】\n卡号: {card_no}\n日文名: {card_info['name_jp']}\n中文名: {card_info['name_cn']}"
    
    def translate_text(self, text: str, card_no: Optional[str] = None) -> str:
        """使用LLM翻译文本"""
        if not text or not text.strip():
            return text
        
        # 构建完整提示
        card_context = self._get_card_context(card_no)
        full_prompt = f"{self.translation_prompt}{card_context}\n\n---\n\n{text}"
        
        # 显示提示词长度（调试用）
        print(f" [提示词: {len(full_prompt)}字符]", end='', flush=True)
        
        try:
            result = self._call_llm(full_prompt)
            return result.strip()
        except Exception as e:
            print(f"  翻译失败: {e}")
            import traceback
            traceback.print_exc()
            return text
    
    def translate_qa_item(self, qa_item: Dict) -> Dict:
        """翻译单个QA条目（带重试）"""
        translated = qa_item.copy()
        card_no = qa_item.get('card_no', '')
        
        print(f" QA#{qa_item.get('qa_number', 'N/A')}", end='', flush=True)
        
        max_retries = 3  # 整个QA最多重试3次
        
        for attempt in range(max_retries):
            try:
                # 翻译问题
                question = qa_item.get('question', '')
                if question:
                    print(" [问题]", end='', flush=True)
                    translated_question = self.translate_text(question, card_no)
                    translated['question'] = translated_question
                    translated['question_original'] = question
                
                # 翻译答案
                answer = qa_item.get('answer', '')
                if answer:
                    print(" [答案]", end='', flush=True)
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
                translated['translation_method'] = f'llm_{self.llm_type}'
                translated['model_used'] = self.model_name  # 记录使用的模型
                
                return translated
                
            except Exception as e:
                error_str = str(e)
                
                # 如果是配额用尽，已经在_call_qwen中处理了模型切换
                # 这里只需要重试
                if "所有Qwen模型配额都已用尽" in error_str:
                    print(f"\n  ❌ 所有模型配额用尽，无法继续")
                    raise
                
                if attempt < max_retries - 1:
                    print(f" [重试整个QA]", end='', flush=True)
                    import time
                    time.sleep(1)
                else:
                    print(f"\n  ❌ QA翻译失败: {e}")
                    # 返回原始数据
                    translated['translation_error'] = str(e)
                    return translated
        
        return translated
    
    def translate_all(self, batch_size: int = 10, delay: float = 1.0, 
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
        if not self.input_qa_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.input_qa_path}")
        
        with open(self.input_qa_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        
        print(f"✓ 加载了 {len(qa_list)} 条QA")
        
        # 加载已翻译的数据（如果存在）
        translated_list = []
        checkpoint_file = self.output_qa_path.parent / f"{self.output_qa_path.stem}_checkpoint.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                translated_list = checkpoint.get('translated', [])
                last_index = checkpoint.get('last_index', -1)
                # 检查索引是否有效
                if last_index >= len(qa_list) - 1:
                    print(f"✓ 检查点显示已完成所有翻译")
                    self._save_final(translated_list)
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()
                    return
                start_from = last_index + 1
            print(f"✓ 从检查点恢复: 已翻译 {len(translated_list)} 条，从第 {start_from + 1} 条继续")
        
        # 确定翻译范围
        end_at = len(qa_list) if max_count is None else min(start_from + max_count, len(qa_list))
        
        # 检查范围是否有效
        if start_from >= len(qa_list):
            print(f"⚠️ 起始位置 {start_from + 1} 超出范围（总共 {len(qa_list)} 条）")
            print(f"✓ 使用已翻译的 {len(translated_list)} 条数据")
            self._save_final(translated_list)
            if checkpoint_file.exists():
                checkpoint_file.unlink()
            return
        
        to_translate = qa_list[start_from:end_at]
        
        print(f"\n开始翻译 (从第 {start_from+1} 条到第 {end_at} 条)...")
        print(f"使用LLM: {self.llm_type}")
        print(f"预计时间: {len(to_translate) * delay / 60:.1f} 分钟")
        print()
        
        # 翻译
        for i, qa_item in enumerate(to_translate, start_from):
            try:
                print(f"[{i+1}/{end_at}] ", end='', flush=True)
                
                translated = self.translate_qa_item(qa_item)
                translated_list.append(translated)
                
                print("✓")
                
                # 显示翻译示例
                if (i + 1) % 10 == 0:
                    print(f"\n示例 - QA #{qa_item.get('qa_number', 'N/A')}:")
                    print(f"  原文: {qa_item.get('question', '')[:50]}...")
                    print(f"  译文: {translated.get('question', '')[:50]}...")
                    print()
                
                # 定期保存检查点
                if (i + 1) % batch_size == 0:
                    self._save_checkpoint(translated_list, i, checkpoint_file)
                    if i + 1 < end_at:
                        time.sleep(delay)
                    
            except KeyboardInterrupt:
                print(f"\n\n用户中断！已保存进度到第 {i} 条")
                self._save_checkpoint(translated_list, i, checkpoint_file)
                return
            except Exception as e:
                print(f"✗ 错误: {e}")
                # 保留原始数据
                translated_list.append(qa_item)
                self._save_checkpoint(translated_list, i, checkpoint_file)
        
        # 最终保存
        self._save_final(translated_list)
        
        # 删除检查点
        if checkpoint_file.exists():
            checkpoint_file.unlink()
        
        print(f"\n✓ 翻译完成！共翻译 {len(translated_list)} 条QA")
        print(f"✓ 输出文件: {self.output_qa_path}")
    
    def _save_checkpoint(self, translated_list: List[Dict], last_index: int, checkpoint_file: Path):
        """保存检查点"""
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            'last_index': last_index,
            'total': len(translated_list),
            'translated': translated_list
        }
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def _save_final(self, translated_list: List[Dict]):
        """保存最终结果"""
        self.output_qa_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_qa_path, 'w', encoding='utf-8') as f:
            json.dump(translated_list, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    print("="*60)
    print("QA翻译工具 - 使用专有名词表")
    print("="*60)
    print()
    
    # 选择LLM
    print("支持的LLM:")
    print("  1. qwen    - 通义千问 (推荐，国内访问快)")
    print("  2. gemini  - Google Gemini")
    print("  3. ollama  - 本地Ollama")
    print()
    
    llm_choice = input("请选择LLM (1/2/3，默认1): ").strip() or "1"
    llm_map = {"1": "qwen", "2": "gemini", "3": "ollama"}
    llm_type = llm_map.get(llm_choice, "qwen")
    
    print(f"\n使用LLM: {llm_type}")
    print()
    
    # 创建翻译器
    try:
        translator = MultiLLMQATranslator(llm_type=llm_type)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n请确保:")
        print("1. 已安装必要的依赖")
        print("2. 已设置对应的API密钥")
        return
    
    # 选择翻译模式
    print("\n翻译模式:")
    print("  1. 测试模式 (翻译前10条)")
    print("  2. 小批量 (翻译前100条)")
    print("  3. 完整翻译 (翻译全部)")
    print()
    
    mode = input("请选择模式 (1/2/3，默认1): ").strip() or "1"
    
    if mode == '1':
        translator.translate_all(batch_size=5, delay=1.0, max_count=10)
    elif mode == '2':
        translator.translate_all(batch_size=10, delay=1.0, max_count=100)
    elif mode == '3':
        confirm = input("\n完整翻译需要较长时间，确认继续? (y/n): ").strip().lower()
        if confirm == 'y':
            translator.translate_all(batch_size=10, delay=1.0)
        else:
            print("已取消")
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
