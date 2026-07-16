"""
Persistent Chroma vector store wrapper.

Uses sentence-transformers embeddings locally (no external embedding API call
needed), which keeps the RAG loop fast and free to run during development/demo.

Supports multiple named collections sharing one Chroma client/embedding
function — used to keep the primary evidence knowledge base and the
precedent/case-study knowledge base separate, since they answer different
questions ("what does the evidence say" vs "what happened elsewhere before").
"""
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from app.utils.logger import logger

_client: Optional["chromadb.PersistentClient"] = None
_embedding_fn = None


def _get_client_and_embedder():
    global _client, _embedding_fn
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
    return _client, _embedding_fn


class VectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        client, embedding_fn = _get_client_and_embedder()
        self._client = client
        self._embedding_fn = embedding_fn
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]) -> int:
        if not texts:
            return 0
        self._collection.add(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Added {len(texts)} chunks to collection '{self.collection_name}'")
        return len(texts)

    def query(self, query_text: str, top_k: Optional[int] = None, where: Optional[Dict[str, Any]] = None):
        top_k = top_k or settings.retrieval_top_k
        return self._collection.query(query_texts=[query_text], n_results=top_k, where=where)

    def count(self) -> int:
        return self._collection.count()

    def reset(self):
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning(f"Vector store collection '{self.collection_name}' reset.")


_stores: Dict[str, VectorStore] = {}


def get_vector_store(collection_name: Optional[str] = None) -> VectorStore:
    """Defaults to the primary evidence collection. Pass settings.precedents_collection_name
    to get the separate precedent/case-study collection instead."""
    name = collection_name or settings.collection_name
    if name not in _stores:
        _stores[name] = VectorStore(name)
    return _stores[name]
