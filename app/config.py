
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    database_url: str = "sqlite:///./data/app.db"

    qdrant_path: str = "./data/qdrant"
    qdrant_collection: str = "documents"

    redis_url: str = "redis://localhost:6379/0"
    chat_history_ttl_seconds: int = 86400
    chat_history_max_turns: int = 20

    embedding_model: str = "all-MiniLM-L6-v2"

    llm_provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    top_k: int = 4

    def ensure_data_dirs(self) -> None:
        Path("./data").mkdir(parents=True, exist_ok=True)
        Path(self.qdrant_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
