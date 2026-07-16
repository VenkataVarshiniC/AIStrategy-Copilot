"""
AI Strategy Copilot — Backend Entrypoint

Boots the FastAPI app, wires up middleware, and mounts route modules.
Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logger import logger
from app.api.routes import analysis, comparison, export, health, ingestion


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Strategy Copilot API",
        description=(
            "Hypothesis-driven consulting engine: decomposes a business question into a "
            "MECE issue tree, grounds each branch in retrieved evidence (RAG), runs "
            "quantitative analysis, red-teams its own recommendation, checks comparable "
            "precedents, and can compare two strategic options head-to-head — exportable "
            "as a client-ready slide deck."
        ),
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(ingestion.router, prefix="/api/ingest", tags=["ingestion"])
    app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(comparison.router, prefix="/api/comparison", tags=["comparison"])
    app.include_router(export.router, prefix="/api/export", tags=["export"])

    @app.on_event("startup")
    async def on_startup():
        logger.info(f"Starting AI Strategy Copilot API in '{settings.app_env}' mode")

    return app


app = create_app()
