"""
Retrieval interface used by the orchestrator.

Converts raw Chroma query results into typed `Evidence` objects so the rest
of the pipeline never touches Chroma's raw dict shape directly.
"""
from typing import List, Optional

from app.models.schemas import Evidence
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger


def retrieve_evidence(query: str, top_k: Optional[int] = None) -> List[Evidence]:
    store = get_vector_store()

    if store.count() == 0:
        logger.warning("Vector store is empty — no evidence will be retrieved. Ingest documents first.")
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
