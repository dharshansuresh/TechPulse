"""
Configuration module for Automotive Engineering AI Assistant.
Loads environment variables safely with defaults and validation.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings(BaseSettings):
    APP_NAME: str = "Automotive Engineering AI Assistant: AUTOSAR HLD Intelligence Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    BASE_DIR: Path = BASE_DIR

    # Server settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    BACKEND_API_URL: str = "http://127.0.0.1:8000"
    STREAMLIT_PORT: int = 8501

    # Storage paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "storage" / "chroma_db"
    DATABASE_PATH: Path = BASE_DIR / "storage" / "app.db"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    # Text Chunking
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 120

    # Embeddings & Vector DB
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHROMA_COLLECTION_NAME: str = "autosar_hld_knowledge"
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.25

    # LLM Settings
    LLM_PROVIDER: str = "auto"  # 'auto', 'openai', 'gemini', 'ollama', 'none'
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = ""  # Can point to Groq, Ollama, DeepSeek, vLLM
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "extra": "ignore"
    }


settings = Settings()

# Ensure critical storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
