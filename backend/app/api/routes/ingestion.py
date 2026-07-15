"""
Ingestion endpoints: load source material (URLs or uploaded PDFs) into the
vector store so the orchestrator has real evidence to retrieve and cite.
"""
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import IngestRequest
from app.rag.ingestion import ingest_pdf, ingest_urls
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger

router = APIRouter()


@router.post("/urls")
def ingest_url_batch(request: IngestRequest):
    if not request.source_urls:
        raise HTTPException(status_code=400, detail="source_urls must be a non-empty list")
    results = ingest_urls(request.source_urls, extra_metadata=request.tags)
    return {"ingested": results, "total_chunks": sum(results.values())}


@router.post("/pdf")
async def ingest_pdf_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported on this endpoint")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        n_chunks = ingest_pdf(tmp_path, source_label=file.filename)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    logger.info(f"Ingested PDF '{file.filename}' -> {n_chunks} chunks")
    return {"filename": file.filename, "chunks_ingested": n_chunks}


@router.get("/status")
def ingestion_status():
    return {"total_chunks": get_vector_store().count()}


@router.delete("/reset")
def reset_knowledge_base():
    get_vector_store().reset()
    return {"status": "reset"}
