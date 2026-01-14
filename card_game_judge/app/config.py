import os
from pathlib import Path
from dotenv import load_dotenv

# 确保从正确的目录加载 .env
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Paths
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
DOCS_DIR = os.getenv("DOCS_DIR", str(BASE_DIR / "data" / "documents"))

# Model settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "local")
LLM_MODEL = os.getenv("LLM_MODEL", "local")  # 可选: local, openai, gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# RAG settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 5

# Collection names
COLLECTION_RULES = "game_rules"
COLLECTION_RULINGS = "official_rulings"
COLLECTION_CASES = "judge_cases"
