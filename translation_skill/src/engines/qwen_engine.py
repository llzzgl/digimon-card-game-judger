"""
通义千问 (Qwen) 翻译引擎
使用阿里云 DashScope API
"""
import os
import time
from typing import Dict, List, Optional

from ..translator import TranslationEngine
from ..config.translation_config import TranslationConfig


class QwenEngine(TranslationEngine):
    """通义千问翻译引擎"""
    
    def __init__(self):
        super().__init__("qwen")
        self.client = None
        self.model_name = TranslationConfig.DEFAULT_QWEN_MODEL
        self.model_index = 0
        self.api_key = TranslationConfig.DASHSCOPE_API_KEY
        self.base_url = TranslationConfig.QWEN_BASE_URL
        self.models = TranslationConfig.QWEN_MODELS
    
    def initialize(self) -> bool:
        """初始化 Qwen 客户端"""
        if not self.api_key:
            return False
        
        try:
            from openai import OpenAI
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.model_name = self.models[self.model_index]
            self.initialized = True
            print(f"  当前模型：{self.model_name}")
            print(f"  可用模型：{', '.join(self.models)}")
            return True
            
        except ImportError:
            print("⚠ 未安装 openai 库：pip install openai")
            return False
        except Exception as e:
            print(f"⚠ Qwen 初始化失败：{e}")
            return False
    
    def _switch_to_next_model(self) -> bool:
        """切换到下一个模型（用于配额用尽时的故障转移）"""
        self.model_index += 1
        if self.model_index >= len(self.models):
            print("\n❌ 所有 Qwen 模型都已用尽配额！")
            return False
        
        self.model_name = self.models[self.model_index]
        print(f"\n⚠️ 切换到模型：{self.model_name}")
        return True
    
    def translate_text(self, text: str, context: Optional[Dict] = None) -> str:
        """
        翻译单个文本
        
        Args:
            text: 待翻译的日文文本
            context: 上下文信息
        
        Returns:
            翻译后的中文文本
        """
        if not self.client:
            raise RuntimeError("Qwen 引擎未初始化")
        
        # 构建提示词
        prompt = self._build_prompt(text, context)
        
        # 调用 API（支持模型切换重试）
        max_retries = TranslationConfig.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是专业的日中游戏规则翻译专家，精通 DTCG 卡牌游戏。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=TranslationConfig.TEMPERATURE,
                    max_tokens=4000,
                    timeout=TranslationConfig.REQUEST_TIMEOUT
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额用尽错误
                if "AllocationQuota" in error_str or "403" in error_str:
                    print(f" 配额用尽")
                    print(f"  ⚠️ 模型 {self.model_name} 免费配额已用尽")
                    
                    # 尝试切换到下一个模型
                    if self._switch_to_next_model():
                        print(f"  ↻ 使用新模型重试...")
                        continue
                    else:
                        raise Exception("所有 Qwen 模型配额都已用尽")
                
                # 其他错误
                if attempt == max_retries - 1:
                    raise
                
                time.sleep(TranslationConfig.RETRY_DELAY * (attempt + 1))
        
        raise RuntimeError("翻译失败，已达到最大重试次数")
    
    def translate_batch(self, texts: List[str], context: Optional[Dict] = None,
                       delay: float = 1.0) -> List[str]:
        """批量翻译文本"""
        results = []
        total = len(texts)
        
        for i, text in enumerate(texts, 1):
            try:
                print(f" [{i}/{total}]", end='', flush=True)
                result = self.translate_text(text, context)
                results.append(result)
                
                # 延迟避免限流
                if i < total and delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f" [错误：{e}]", end='', flush=True)
                results.append(text)  # 保留原文
        
        return results
    
    def _build_prompt(self, text: str, context: Optional[Dict] = None) -> str:
        """构建翻译提示词"""
        prompt_parts = []
        
        # 基础翻译指令
        prompt_parts.append("""请将以下日文游戏规则翻译成中文。

重要要求：
1. 使用提供的术语对照表中的中文术语（如有）
2. 保持专业、准确的翻译风格
3. 保留原文的格式和结构
4. 数字、符号保持不变
5. 确保游戏规则的逻辑清晰
6. 完全翻译，不要保留任何日文假名或汉字""")
        
        # 添加术语表
        if context and "terminology" in context:
            term_list = context["terminology"]
            if isinstance(term_list, dict):
                terms_text = "\n".join([f"  {jp} → {cn}" for jp, cn in list(term_list.items())[:50]])
                prompt_parts.append(f"\n术语对照表参考（部分）：\n{terms_text}")
        
        # 添加卡牌上下文
        if context and "card_info" in context:
            card_info = context["card_info"]
            prompt_parts.append(f"\n卡牌信息：\n卡号：{card_info.get('card_no', '')}\n日文名：{card_info.get('name_jp', '')}\n中文名：{card_info.get('name_cn', '')}")
        
        # 添加待翻译文本
        prompt_parts.append(f"\n待翻译的日文内容：\n{text}")
        prompt_parts.append("\n请直接输出翻译后的中文内容。")
        
        return "\n\n".join(prompt_parts)
