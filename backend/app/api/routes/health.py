"""Simple liveness/readiness endpoint."""
import requests
from fastapi import APIRouter

from app.config import settings
from app.rag.vector_store import get_vector_store

router = APIRouter()


@router.get("/")
def health_check():
    try:
        doc_count = get_vector_store().count()
        vector_store_status = "ok"
    except Exception as e:
        doc_count = None
        vector_store_status = f"error: {e}"

    try:
        resp = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        resp.raise_for_status()
        pulled_models = [m["name"] for m in resp.json().get("models", [])]
        ollama_status = "ok" if settings.ollama_model in pulled_models or any(
            m.startswith(settings.ollama_model) for m in pulled_models
        ) else f"reachable, but '{settings.ollama_model}' not pulled yet (run: ollama pull {settings.ollama_model})"
    except requests.exceptions.RequestException:
        ollama_status = f"unreachable at {settings.ollama_base_url} — is `ollama serve` running?"

    return {
        "status": "ok",
        "app_env": settings.app_env,
        "ollama_model": settings.ollama_model,
        "ollama_status": ollama_status,
        "vector_store_status": vector_store_status,
        "ingested_chunks": doc_count,
    }
