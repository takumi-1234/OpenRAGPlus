# rag-python/app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .envファイルから読み込む設定
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # RAG Service Settings
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    EMBEDDING_MODEL_NAME: str = "retrieva-jp/amber-large"

    # Directory Paths (in container)
    CHROMA_DB_PATH: str = "/app/data/chroma"
    UPLOAD_DIR: str = "/app/static/uploads"

    # Authentication
    JWT_SECRET_KEY: str

settings = Settings()