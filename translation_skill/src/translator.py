"""
翻译统一接口
Unified Translation Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import time


class TranslationEngine(ABC):
    """翻译引擎基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化引擎"""
        pass
    
    @abstractmethod
    def translate_text(self, text: str, context: Optional[Dict] = None) -> str:
        """
        翻译文本
        
        Args:
            text: 待翻译的文本
            context: 上下文信息（如术语表、卡牌信息等）
        
        Returns:
            翻译后的文本
        """
        pass
    
    @abstractmethod
    def translate_batch(self, texts: List[str], context: Optional[Dict] = None) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译的文本列表
            context: 上下文信息
        
        Returns:
            翻译后的文本列表
        """
        pass
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self.initialized


class Translator:
    """
    翻译器主类
    统一管理多个翻译引擎
    """
    
    def __init__(self, default_engine: str = "openai"):
        """
        初始化翻译器
        
        Args:
            default_engine: 默认使用的引擎 ('openai', 'gemini', 'qwen')
        """
        self.default_engine = default_engine
        self.engines: Dict[str, TranslationEngine] = {}
        self._register_engines()
    
    def _register_engines(self):
        """注册所有可用的翻译引擎"""
        # 延迟导入以避免循环依赖
        from .engines.openai_engine import OpenAIEngine
        from .engines.gemini_engine import GeminiEngine
        from .engines.qwen_engine import QwenEngine
        
        # 注册引擎
        self.engines["openai"] = OpenAIEngine()
        self.engines["gemini"] = GeminiEngine()
        self.engines["qwen"] = QwenEngine()
        
        # 初始化引擎
        for name, engine in self.engines.items():
            try:
                if engine.initialize():
                    print(f"✓ 引擎 '{name}' 已初始化")
                else:
                    print(f"⚠ 引擎 '{name}' 初始化失败（可能缺少 API 密钥）")
            except Exception as e:
                print(f"⚠ 引擎 '{name}' 初始化失败：{e}")
    
    def get_engine(self, engine_name: Optional[str] = None) -> Optional[TranslationEngine]:
        """
        获取指定引擎
        
        Args:
            engine_name: 引擎名称，如 None 则使用默认引擎
        
        Returns:
            翻译引擎实例，如不可用则返回 None
        """
        name = engine_name or self.default_engine
        engine = self.engines.get(name)
        
        if engine and engine.is_available():
            return engine
        
        # 如果默认引擎不可用，尝试其他引擎
        for eng_name, eng in self.engines.items():
            if eng.is_available():
                print(f"⚠ 引擎 '{name}' 不可用，切换到 '{eng_name}'")
                return eng
        
        return None
    
    def translate(self, text: str, engine: Optional[str] = None, 
                  context: Optional[Dict] = None) -> str:
        """
        使用指定引擎翻译文本
        
        Args:
            text: 待翻译的文本
            engine: 引擎名称（可选）
            context: 上下文信息
        
        Returns:
            翻译后的文本
        """
        eng = self.get_engine(engine)
        
        if not eng:
            raise RuntimeError("没有可用的翻译引擎，请检查 API 密钥配置")
        
        return eng.translate_text(text, context)
    
    def translate_batch(self, texts: List[str], engine: Optional[str] = None,
                       context: Optional[Dict] = None, 
                       delay: float = 1.0) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译的文本列表
            engine: 引擎名称（可选）
            context: 上下文信息
            delay: 每批之间的延迟（秒）
        
        Returns:
            翻译后的文本列表
        """
        eng = self.get_engine(engine)
        
        if not eng:
            raise RuntimeError("没有可用的翻译引擎")
        
        return eng.translate_batch(texts, context)
    
    def list_engines(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的引擎及其状态
        
        Returns:
            引擎信息列表
        """
        result = []
        for name, engine in self.engines.items():
            result.append({
                "name": name,
                "available": engine.is_available(),
                "initialized": engine.initialized
            })
        return result
