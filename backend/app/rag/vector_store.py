"""
Persistent Chroma vector store wrapper.

Uses sentence-transformers embeddings locally (no external embedding API call
needed), which keeps the RAG loop fast and free to run during development/demo.
"""
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from app.utils.logger import logger


class VectorStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]) -> int:
        if not texts:
            return 0
        self._collection.add(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Added {len(texts)} chunks to collection '{settings.collection_name}'")
        return len(texts)

    def query(self, query_text: str, top_k: Optional[int] = None, where: Optional[Dict[str, Any]] = None):
        top_k = top_k or settings.retrieval_top_k
        results = self._collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where,
        )
        return results

    def count(self) -> int:
        return self._collection.count()

    def reset(self):
        self._client.delete_collection(settings.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("Vector store collection reset.")


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
