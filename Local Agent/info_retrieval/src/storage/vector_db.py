from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ir_utils.config import AppConfig
from ir_utils.logger import get_logger

logger = get_logger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
except ImportError:  # pragma: no cover - environment dependent
    QdrantClient = None
    Distance = FieldCondition = Filter = MatchValue = PointStruct = VectorParams = None


class VectorDB:
    """
    Qdrant-backed vector store with an in-memory fallback for tests.
    """

    def __init__(self, config: AppConfig, use_in_memory: bool = False) -> None:
        self.config = config
        self.use_in_memory = use_in_memory or QdrantClient is None
        self._memory_store: Optional[InMemoryVectorStore] = None
        self._client: Optional[Any] = None

        if self.use_in_memory:
            logger.warning("Using in-memory vector store; start Qdrant for persistence.")
            self._memory_store = InMemoryVectorStore()
        else:
            host = os.getenv("QDRANT_HOST")
            port = int(os.getenv("QDRANT_PORT", "6333"))
            if host:
                self._client = QdrantClient(host=host, port=port)
            else:
                self._client = QdrantClient(path=str(config.vector_db_path))

    def initialize_collections(self, company_id: str, vector_size: int) -> Tuple[str, str]:
        """
        Ensure both content and style collections exist for a company.
        """
        content_collection = self._collection_name("content", company_id)
        style_collection = self._collection_name("style", company_id)

        if self.use_in_memory:
            assert self._memory_store is not None
            self._memory_store.initialize_collection(content_collection, vector_size)
            self._memory_store.initialize_collection(style_collection, vector_size)
            return content_collection, style_collection

        assert self._client is not None and Distance and VectorParams
        existing = [c.name for c in self._client.get_collections().collections]  # type: ignore
        for collection in (content_collection, style_collection):
            if collection not in existing:
                self._client.create_collection(  # type: ignore
                    collection_name=collection,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
        return content_collection, style_collection

    def insert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
        company_id: str,
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length.")
        if len(metadata) != len(chunks):
            raise ValueError("Metadata length must match number of chunks.")

        for chunk, vector, meta in zip(chunks, embeddings, metadata):
            chunk_type = meta.get("chunk_type") or chunk.get("chunk_type")
            if chunk_type not in {"content", "style"}:
                raise ValueError("chunk_type must be 'content' or 'style'")
            collection_name = self._collection_name(str(chunk_type), company_id)
            payload = {"text": chunk.get("text", ""), **{k: v for k, v in chunk.items() if k != "text"}, **meta}
            self._upsert_point(collection_name, payload, vector)

    def search(
        self, query_vector: List[float], company_id: str, chunk_type: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        collection_name = self._collection_name(chunk_type, company_id)
        if self.use_in_memory:
            assert self._memory_store is not None
            return self._memory_store.search(collection_name, query_vector, top_k)

        assert self._client is not None
        results = self._client.search(  # type: ignore
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
        )
        return [_format_qdrant_result(r) for r in results]

    def search_with_filters(
        self,
        query_vector: List[float],
        company_id: str,
        chunk_type: str,
        filters: Dict[str, Any],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        collection_name = self._collection_name(chunk_type, company_id)
        if self.use_in_memory:
            assert self._memory_store is not None
            return self._memory_store.search(collection_name, query_vector, top_k, filters)

        assert self._client is not None and Filter
        conditions = []
        for field, value in filters.items():
            conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))  # type: ignore
        qdrant_filter = Filter(must=conditions)  # type: ignore

        results = self._client.search(  # type: ignore
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
        )
        return [_format_qdrant_result(r) for r in results]

    def _upsert_point(self, collection_name: str, payload: Dict[str, Any], vector: List[float]) -> None:
        point_id = payload.get("chunk_id") or str(uuid.uuid4())

        if self.use_in_memory:
            assert self._memory_store is not None
            self._memory_store.insert(collection_name, payload, vector, point_id)
            return

        assert self._client is not None and PointStruct
        point = PointStruct(id=point_id, vector=vector, payload=payload)  # type: ignore
        self._client.upsert(collection_name=collection_name, points=[point], wait=True)  # type: ignore

    def _collection_name(self, chunk_type: str, company_id: str) -> str:
        if chunk_type not in {"content", "style"}:
            raise ValueError("chunk_type must be 'content' or 'style'")
        return f"{chunk_type}_{company_id}"


class InMemoryVectorStore:
    """
    Lightweight in-memory vector store for testing.
    """

    def __init__(self) -> None:
        self.collections: Dict[str, Dict[str, Any]] = {}

    def initialize_collection(self, name: str, vector_size: int) -> None:
        self.collections[name] = {"vector_size": vector_size, "points": {}}

    def insert(self, collection_name: str, payload: Dict[str, Any], vector: List[float], point_id: str) -> None:
        collection = self.collections.get(collection_name)
        if collection is None:
            raise ValueError(f"Collection {collection_name} not initialized.")
        vector_array = np.asarray(vector, dtype=float)
        collection["points"][point_id] = {"vector": vector_array, "payload": payload}

    def search(
        self, collection_name: str, query_vector: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        collection = self.collections.get(collection_name)
        if collection is None or not collection["points"]:
            return []
        query = np.asarray(query_vector, dtype=float)
        results = []
        for point_id, record in collection["points"].items():
            if filters and not _matches_filters(record["payload"], filters):
                continue
            score = _cosine_similarity(query, record["vector"])
            results.append({"id": point_id, "score": float(score), "payload": record["payload"]})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]


def _format_qdrant_result(result: Any) -> Dict[str, Any]:
    return {"id": str(result.id), "score": float(result.score), "payload": result.payload}


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _matches_filters(payload: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    for key, expected in filters.items():
        if payload.get(key) != expected:
            return False
    return True
