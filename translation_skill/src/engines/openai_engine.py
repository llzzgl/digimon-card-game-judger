"""
OpenAI 翻译引擎
支持 OpenAI 官方 API 及兼容接口（如 Qwen）
"""
import os
import time
import httpx
from typing import Dict, List, Optional
from pathlib import Path

from ..translator import TranslationEngine
from ..config.translation_config import TranslationConfig


class OpenAIEngine(TranslationEngine):
    """OpenAI 翻译引擎"""
    
    def __init__(self):
        super().__init__("openai")
        self.client = None
        self.model = TranslationConfig.OPENAI_MODEL
        self.base_url = TranslationConfig.OPENAI_BASE_URL
        self.api_key = TranslationConfig.OPENAI_API_KEY
    
    def initialize(self) -> bool:
        """初始化 OpenAI 客户端"""
        if not self.api_key:
            return False
        
        try:
            from openai import OpenAI
            
            # 配置 HTTP 客户端（支持代理）
            http_client = None
            if TranslationConfig.USE_PROXY:
                http_client = httpx.Client(proxy=TranslationConfig.PROXY_URL)
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )
            self.initialized = True
            return True
            
        except ImportError:
            print("⚠ 未安装 openai 库：pip install openai")
            return False
        except Exception as e:
            print(f"⚠ OpenAI 初始化失败：{e}")
            return False
    
    def translate_text(self, text: str, context: Optional[Dict] = None) -> str:
        """
        翻译单个文本
        
        Args:
            text: 待翻译的日文文本
            context: 上下文信息（术语表、卡牌信息等）
        
        Returns:
            翻译后的中文文本
        """
        if not self.client:
            raise RuntimeError("OpenAI 引擎未初始化")
        
        # 构建提示词
        prompt = self._build_prompt(text, context)
        
        # 调用 API
        for attempt in range(TranslationConfig.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
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
                if attempt == TranslationConfig.MAX_RETRIES - 1:
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
            elif isinstance(term_list, list):
                terms_text = "\n".join([f"  {t}" for t in term_list[:50]])
                prompt_parts.append(f"\n术语参考（部分）：\n{terms_text}")
        
        # 添加卡牌上下文
        if context and "card_info" in context:
            card_info = context["card_info"]
            prompt_parts.append(f"\n卡牌信息：\n卡号：{card_info.get('card_no', '')}\n日文名：{card_info.get('name_jp', '')}\n中文名：{card_info.get('name_cn', '')}")
        
        # 添加待翻译文本
        prompt_parts.append(f"\n待翻译的日文内容：\n{text}")
        prompt_parts.append("\n请直接输出翻译后的中文内容。")
        
        return "\n\n".join(prompt_parts)
