"""
Ingestion pipeline: pulls raw content (URLs, PDFs, plain text), chunks it,
and writes it into the vector store with source metadata so every retrieved
snippet can later be cited back to a real source.
"""
import hashlib
import uuid
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.config import settings
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger


def _chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


def fetch_url_text(url: str) -> str:
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (StrategyCopilot/0.1)"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def ingest_text(text: str, source: str, extra_metadata: Dict[str, Any] = None) -> int:
    extra_metadata = extra_metadata or {}
    chunks = _chunk_text(text)
    ids, docs, metas = [], [], []
    for i, chunk in enumerate(chunks):
        chunk_hash = hashlib.sha1(f"{source}-{i}".encode()).hexdigest()[:12]
        ids.append(f"{chunk_hash}-{uuid.uuid4().hex[:6]}")
        docs.append(chunk)
        metas.append({"source": source, "chunk_index": i, **extra_metadata})

    store = get_vector_store()
    return store.add_documents(ids=ids, texts=docs, metadatas=metas)


def ingest_urls(urls: List[str], extra_metadata: Dict[str, Any] = None) -> Dict[str, int]:
    results = {}
    for url in urls:
        try:
            text = fetch_url_text(url)
            n = ingest_text(text, source=url, extra_metadata=extra_metadata)
            results[url] = n
            logger.info(f"Ingested {n} chunks from {url}")
        except Exception as e:
            logger.error(f"Failed to ingest {url}: {e}")
            results[url] = 0
    return results


def ingest_pdf(file_path: str, source_label: str = None, extra_metadata: Dict[str, Any] = None) -> int:
    text = extract_pdf_text(file_path)
    return ingest_text(text, source=source_label or file_path, extra_metadata=extra_metadata)
