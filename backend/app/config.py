"""
Central application configuration.
Loaded once as a singleton (`settings`) and imported everywhere else.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Groq API — free tier, no credit card. Get a key at https://console.groq.com
    groq_api_key: str = ""
    # llama-3.1-8b-instant has a much higher free-tier requests/day and
    # tokens/minute budget than the 70b model, which matters a lot for this
    # pipeline (6+ sequential LLM calls per analysis run). Swap to
    # llama-3.3-70b-versatile for stronger reasoning if you have headroom.
    groq_model: str = "llama-3.1-8b-instant"
    # Minimum delay between sequential Groq calls within one analysis run.
    # The pipeline fires ~6+ calls back to back (issue tree + N branches +
    # synthesis); without pacing, this can burst past the free tier's
    # tokens-per-minute cap partway through a single request. This is a
    # blunt but effective safeguard on top of the retry/backoff in groq_client.
    groq_request_delay_seconds: float = 1.5

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Vector store
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "strategy_copilot_docs"
    precedents_collection_name: str = "strategy_copilot_precedents"

    # Retrieval — kept modest to control per-call token usage against the
    # free-tier TPM budget (each extra evidence snippet adds prompt tokens
    # on every single branch's hypothesis-testing call).
    retrieval_top_k: int = 4
    chunk_size: int = 800
    chunk_overlap: int = 120

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
