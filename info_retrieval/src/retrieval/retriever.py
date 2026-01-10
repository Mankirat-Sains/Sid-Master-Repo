from __future__ import annotations

from typing import Any, Dict, List, Optional

from embeddings.embedding_service import EmbeddingService
from storage.vector_store import VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    High-level retrieval interface to embed queries and search stored chunks.
    """

    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata_list: List[Dict[str, Any]],
        company_id: str,
    ) -> None:
        texts = [chunk.get("text", "") for chunk in chunks]
        vectors = self.embedding_service.embed_batch(texts)
        if not vectors:
            logger.warning("No vectors generated; skipping index.")
            return

        from ..storage.vector_store import Chunk as VSChunk

        chunk_payloads: List[VSChunk] = []
        for chunk, meta, vector in zip(chunks, metadata_list, vectors):
            payload = {
                **meta,
                "text": chunk.get("text", ""),
                "chunk_type": meta.get("chunk_type") or chunk.get("chunk_type"),
                "index_type": meta.get("chunk_type") or chunk.get("chunk_type"),
                "company_id": company_id,
            }
            chunk_payloads.append(
                VSChunk(
                    id=payload.get("chunk_id", ""),
                    text=payload["text"],
                    embedding=vector,
                    metadata=payload,
                )
            )
        self.vector_store.upsert(chunk_payloads)

    def retrieve_for_query(
        self,
        query_text: str,
        company_id: str,
        chunk_type: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query_vector = self.embedding_service.embed_text(query_text)
        if not query_vector:
            return []
        filters = filters or {}
        filters.setdefault("company_id", company_id)
        filters["index_type"] = chunk_type
        results = self.vector_store.search(query_vector, top_k=top_k, filters=filters)
        return [_format_result_from_store(r) for r in results]

    def retrieve_content(
        self, query_text: str, company_id: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return self.retrieve_for_query(query_text, company_id, chunk_type="content", top_k=top_k, filters=filters)

    def retrieve_style_examples(
        self, section_type: Optional[str], company_id: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        filters = {"section_type": section_type} if section_type else None
        query = section_type or "style exemplar"
        return self.retrieve_for_query(query, company_id, chunk_type="style", top_k=top_k, filters=filters)

    def retrieve_by_metadata(
        self, query_text: str, company_id: str, chunk_type: str, top_k: int = 5, **filters: Any
    ) -> List[Dict[str, Any]]:
        return self.retrieve_for_query(query_text, company_id, chunk_type=chunk_type, top_k=top_k, filters=filters)


def _format_result_from_store(result: Any) -> Dict[str, Any]:
    payload = result.metadata if hasattr(result, "metadata") else result.get("metadata", {})
    text = result.text if hasattr(result, "text") else result.get("text", "")
    score = result.score if hasattr(result, "score") else result.get("score", 0.0)
    rid = result.id if hasattr(result, "id") else result.get("id")
    return {"id": rid, "score": score, "text": text, "metadata": payload}
