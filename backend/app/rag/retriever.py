"""
Retrieval interface used by the orchestrator.

Converts raw Chroma query results into typed `Evidence` objects so the rest
of the pipeline never touches Chroma's raw dict shape directly.
"""
from typing import List, Optional

from app.config import settings
from app.models.schemas import Evidence
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger


def _query_collection(query: str, collection_name: Optional[str], top_k: Optional[int], empty_warning: str) -> List[Evidence]:
    store = get_vector_store(collection_name)

    if store.count() == 0:
        logger.warning(empty_warning)
        return []

    results = store.query(query_text=query, top_k=top_k)

    evidence: List[Evidence] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # Chroma cosine distance -> similarity score (higher is better)
        score = round(1 - dist, 4) if dist is not None else 0.0
        evidence.append(
            Evidence(
                source=meta.get("source", "unknown"),
                snippet=doc[:600],
                score=score,
                metadata=meta,
            )
        )
    return evidence


def retrieve_evidence(query: str, top_k: Optional[int] = None) -> List[Evidence]:
    return _query_collection(
        query,
        collection_name=None,  # primary evidence collection
        top_k=top_k,
        empty_warning="Vector store is empty — no evidence will be retrieved. Ingest documents first.",
    )


def retrieve_precedents(query: str, top_k: Optional[int] = 3) -> List[Evidence]:
    """Queries the separate precedent/case-study collection. Returns [] silently
    (not an error) if nothing's been ingested there — precedents are a bonus
    layer, not a required one, unlike primary evidence."""
    return _query_collection(
        query,
        collection_name=settings.precedents_collection_name,
        top_k=top_k,
        empty_warning="No precedents ingested — skipping precedent analysis for this run.",
    )
