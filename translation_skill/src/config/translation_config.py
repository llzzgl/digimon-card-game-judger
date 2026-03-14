"""
翻译配置文件
Translation Configuration
"""
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class TranslationConfig:
    """翻译配置类"""
    
    # ========== 路径配置 ==========
    # 基础目录
    BASE_DIR = Path(__file__).parent.parent  # src/
    
    # 数据目录
    DATA_DIR = BASE_DIR.parent / "data"  # translation_skill/data/
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    TERMINOLOGY_DIR = DATA_DIR / "terminology"
    
    # 输出到原项目的路径（保持一致）
    # translation_skill/ -> dtcg_judger/ -> skill/data/
    PROJECT_ROOT = BASE_DIR.parent.parent  # dtcg_judger/
    SKILL_DATA_DIR = PROJECT_ROOT / "skill" / "data"
    
    # ========== API 配置 ==========
    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Gemini 配置
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    # Qwen (通义千问) 配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODELS = [
        "qwen-turbo",      # 快速、便宜
        "qwen-plus",       # 平衡
        "qwen-max",        # 高质量
        "qwen-long",       # 长文本
    ]
    DEFAULT_QWEN_MODEL = "qwen-plus"
    
    # ========== 代理配置 ==========
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
    PROXY_PORT = os.getenv("PROXY_PORT", "7890")
    PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}"
    
    # ========== 翻译配置 ==========
    # 分块大小（字符数）
    RULEBOOK_CHUNK_SIZE = 2500
    QA_CHUNK_SIZE = 2000
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # 秒
    REQUEST_TIMEOUT = 60  # 秒
    
    # 温度参数
    TEMPERATURE = 0.3
    
    # 批量处理配置
    BATCH_SIZE = 10
    BATCH_DELAY = 1.0  # 秒
    
    # ========== 术语表配置 ==========
    # 默认术语表路径（从原项目复制）
    DEFAULT_TERMINOLOGY_PATHS = [
        PROJECT_ROOT / "digimon_card_data" / "term_mapping" / "game_mechanics_keywords.json",
        PROJECT_ROOT / "digimon_card_data" / "term_mapping" / "llm_keywords_cn_jp.json",
        PROJECT_ROOT / "digimon_card_data" / "term_mapping" / "basic_terms_cn_jp.json",
    ]
    
    # ========== 输出文件配置 ==========
    # 规则书翻译输出
    RULEBOOK_OUTPUT_FILE = "rules.txt"
    
    # QA 翻译输出
    QA_OUTPUT_FILE = "rulings.json"
    
    # 术语表输出
    TERMS_OUTPUT_FILE = "terms.json"
    
    @classmethod
    def get_proxy_url(cls) -> Optional[str]:
        """获取代理 URL"""
        return cls.PROXY_URL if cls.USE_PROXY else None
    
    @classmethod
    def get_output_path(cls, file_type: str) -> Path:
        """
        获取输出文件路径
        
        Args:
            file_type: 文件类型 ('rules', 'rulings', 'terms')
        
        Returns:
            输出文件路径
        """
        if file_type == "rules":
            return cls.SKILL_DATA_DIR / cls.RULEBOOK_OUTPUT_FILE
        elif file_type == "rulings":
            return cls.SKILL_DATA_DIR / cls.QA_OUTPUT_FILE
        elif file_type == "terms":
            return cls.SKILL_DATA_DIR / cls.TERMS_OUTPUT_FILE
        else:
            raise ValueError(f"未知的文件类型：{file_type}")
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必要的目录存在"""
        cls.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.TERMINOLOGY_DIR.mkdir(parents=True, exist_ok=True)
        cls.SKILL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_api_keys(cls, engine_type: str) -> bool:
        """
        验证 API 密钥是否配置
        
        Args:
            engine_type: 引擎类型 ('openai', 'gemini', 'qwen')
        
        Returns:
            是否配置有效
        """
        if engine_type == "openai":
            return bool(cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("your"))
        elif engine_type == "gemini":
            return bool(cls.GEMINI_API_KEY and not cls.GEMINI_API_KEY.startswith("your"))
        elif engine_type == "qwen":
            return bool(cls.DASHSCOPE_API_KEY and not cls.DASHSCOPE_API_KEY.startswith("your"))
        else:
            return False


# 创建必要的目录
TranslationConfig.ensure_directories()
