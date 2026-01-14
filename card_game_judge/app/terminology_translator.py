"""
术语翻译器 - 支持中日双向翻译
用于查询时将中文转日文，返回时将日文转中文
"""
import json
import re
from pathlib import Path
from typing import Dict, Tuple


class TerminologyTranslator:
    def __init__(self):
        self.zh_to_ja: Dict[str, str] = {}  # 中文 → 日文
        self.ja_to_zh: Dict[str, str] = {}  # 日文 → 中文
        self._load_terminology()
    
    def _load_terminology(self):
        """加载术语对照表"""
        base_dir = Path(__file__).parent.parent.parent
        
        # 加载术语对照表
        terminology_file = base_dir / "digimon_data" / "dtcg_terminology.json"
        if terminology_file.exists():
            with open(terminology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category, terms in data.items():
                    if isinstance(terms, dict):
                        for ja, zh in terms.items():
                            if ja and zh:
                                self.ja_to_zh[ja] = zh
                                self.zh_to_ja[zh] = ja
        
        # 加载数码宝贝名称对照表
        name_file = base_dir / "digimon_data" / "digimon_name_mapping.json"
        if name_file.exists():
            with open(name_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for ja, zh in data.items():
                    if ja and zh:
                        self.ja_to_zh[ja] = zh
                        self.zh_to_ja[zh] = ja
        
        print(f"[术语翻译器] 加载完成: {len(self.zh_to_ja)} 条中→日, {len(self.ja_to_zh)} 条日→中")
    
    def translate_query_to_japanese(self, query: str) -> Tuple[str, list]:
        """
        将查询中的中文术语转换为日文
        返回: (翻译后的查询, 翻译记录列表)
        """
        translated = query
        translations = []
        
        # 按长度降序排序，优先匹配长词
        sorted_terms = sorted(self.zh_to_ja.keys(), key=len, reverse=True)
        
        for zh_term in sorted_terms:
            if zh_term in translated:
                ja_term = self.zh_to_ja[zh_term]
                translated = translated.replace(zh_term, ja_term)
                translations.append((zh_term, ja_term))
        
        return translated, translations
    
    def translate_result_to_chinese(self, text: str) -> str:
        """将结果中的日文术语转换为中文"""
        translated = text
        
        # 按长度降序排序，优先匹配长词
        sorted_terms = sorted(self.ja_to_zh.keys(), key=len, reverse=True)
        
        for ja_term in sorted_terms:
            if ja_term in translated:
                zh_term = self.ja_to_zh[ja_term]
                translated = translated.replace(ja_term, zh_term)
        
        return translated
    
    def expand_query(self, query: str) -> str:
        """
        扩展查询：同时包含中文和对应的日文术语
        这样可以同时匹配中文和日文的向量
        """
        ja_query, translations = self.translate_query_to_japanese(query)
        
        if translations:
            # 组合原始查询和翻译后的查询
            return f"{query} {ja_query}"
        return query


# 单例
terminology_translator = TerminologyTranslator()
