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

    if not settings.groq_api_key:
        groq_status = "GROQ_API_KEY not set — get a free key at https://console.groq.com"
    else:
        try:
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                timeout=5,
            )
            if resp.status_code == 401:
                groq_status = "API key rejected — double check GROQ_API_KEY"
            else:
                resp.raise_for_status()
                available = [m["id"] for m in resp.json().get("data", [])]
                groq_status = "ok" if settings.groq_model in available else (
                    f"reachable, but '{settings.groq_model}' not found in your account's model list"
                )
        except requests.exceptions.RequestException as e:
            groq_status = f"unreachable: {e}"

    return {
        "status": "ok",
        "app_env": settings.app_env,
        "groq_model": settings.groq_model,
        "groq_status": groq_status,
        "vector_store_status": vector_store_status,
        "ingested_chunks": doc_count,
    }
