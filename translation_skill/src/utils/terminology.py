"""
术语管理工具
Terminology Management Utilities
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from ..config.translation_config import TranslationConfig


class TerminologyManager:
    """术语管理器"""
    
    def __init__(self, terminology_paths: Optional[List[Path]] = None):
        """
        初始化术语管理器
        
        Args:
            terminology_paths: 术语表文件路径列表
        """
        self.paths = terminology_paths or TranslationConfig.DEFAULT_TERMINOLOGY_PATHS
        self.terminology: Dict[str, str] = {}
        self.reverse_terminology: Dict[str, str] = {}
        self.loaded = False
    
    def load_all(self) -> Dict[str, str]:
        """
        加载所有术语表
        
        Returns:
            合并后的术语字典（日文 -> 中文）
        """
        all_terms = {}
        
        for path in self.paths:
            if not path.exists():
                print(f"⚠ 术语表不存在：{path}")
                continue
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 解析术语表（支持多种格式）
                terms = self._parse_terminology_file(data)
                all_terms.update(terms)
                print(f"✓ 加载术语表：{path.name} ({len(terms)} 个术语)")
                
            except Exception as e:
                print(f"⚠ 加载术语表失败 {path.name}: {e}")
        
        self.terminology = all_terms
        
        # 构建反向索引（中文 -> 日文）
        self.reverse_terminology = {cn: jp for jp, cn in all_terms.items()}
        
        self.loaded = True
        print(f"\n总计加载 {len(self.terminology)} 个术语")
        
        return self.terminology
    
    def _parse_terminology_file(self, data: dict) -> Dict[str, str]:
        """
        解析术语表文件
        
        支持格式：
        1. {"中文术语": ["日文术语 1", "日文术语 2"]}
        2. {"日文术语": "中文术语"}
        3. {"category": {"term": "translation"}}
        
        Args:
            data: JSON 数据
        
        Returns:
            日文 -> 中文的术语字典
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                # 格式：{"中文": ["日文 1", "日文 2"]}
                chinese = key
                japanese_list = value
                for jp in japanese_list:
                    result[jp] = chinese
            elif isinstance(value, str):
                # 格式：{"日文": "中文"}
                result[key] = value
            elif isinstance(value, dict):
                # 格式：{"category": {"term": "translation"}}
                nested = self._parse_terminology_file(value)
                result.update(nested)
        
        return result
    
    def get_term(self, japanese: str) -> Optional[str]:
        """
        获取日文术语对应的中文翻译
        
        Args:
            japanese: 日文术语
        
        Returns:
            中文翻译，如不存在则返回 None
        """
        if not self.loaded:
            self.load_all()
        
        # 精确匹配
        if japanese in self.terminology:
            return self.terminology[japanese]
        
        # 尝试部分匹配（长术语优先）
        sorted_terms = sorted(self.terminology.keys(), key=len, reverse=True)
        for jp_term in sorted_terms:
            if jp_term in japanese:
                return self.terminology[jp_term]
        
        return None
    
    def replace_terminology(self, text: str) -> str:
        """
        替换文本中的术语
        
        Args:
            text: 待替换的文本
        
        Returns:
            替换后的文本
        """
        if not self.loaded:
            self.load_all()
        
        result = text
        
        # 按长度降序排序，优先匹配长术语
        sorted_terms = sorted(self.terminology.items(), key=lambda x: len(x[0]), reverse=True)
        
        for jp_term, cn_term in sorted_terms:
            result = result.replace(jp_term, cn_term)
        
        return result
    
    def export_terms(self, output_path: Path, format: str = "json") -> None:
        """
        导出术语表
        
        Args:
            output_path: 输出文件路径
            format: 输出格式 ('json', 'txt')
        """
        if not self.loaded:
            self.load_all()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.terminology, f, ensure_ascii=False, indent=2)
        elif format == "txt":
            with open(output_path, 'w', encoding='utf-8') as f:
                for jp, cn in sorted(self.terminology.items()):
                    f.write(f"{jp} → {cn}\n")
        
        print(f"✓ 术语表已导出：{output_path}")
    
    def add_term(self, japanese: str, chinese: str) -> None:
        """
        添加新术语
        
        Args:
            japanese: 日文术语
            chinese: 中文翻译
        """
        self.terminology[japanese] = chinese
        self.reverse_terminology[chinese] = japanese
    
    def get_statistics(self) -> Dict:
        """
        获取术语统计信息
        
        Returns:
            统计信息字典
        """
        if not self.loaded:
            self.load_all()
        
        return {
            "total_terms": len(self.terminology),
            "source_files": len(self.paths),
            "files_loaded": sum(1 for p in self.paths if p.exists())
        }


def load_terminology_from_project(project_root: Path) -> TerminologyManager:
    """
    从项目加载术语表
    
    Args:
        project_root: 项目根目录
    
    Returns:
        术语管理器实例
    """
    default_paths = [
        project_root / "digimon_card_data" / "term_mapping" / "game_mechanics_keywords.json",
        project_root / "digimon_card_data" / "term_mapping" / "llm_keywords_cn_jp.json",
        project_root / "digimon_card_data" / "term_mapping" / "basic_terms_cn_jp.json",
    ]
    
    manager = TerminologyManager(default_paths)
    manager.load_all()
    
    return manager
