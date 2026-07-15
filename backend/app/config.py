"""
Central application configuration.
Loaded once as a singleton (`settings`) and imported everywhere else.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Local LLM (Ollama) — no API key needed, runs on your own machine
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Vector store
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "strategy_copilot_docs"

    # Retrieval
    retrieval_top_k: int = 6
    chunk_size: int = 800
    chunk_overlap: int = 120

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
