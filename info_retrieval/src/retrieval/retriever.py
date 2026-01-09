from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..embeddings.embedding_service import EmbeddingService
from ..storage.vector_db import VectorDB
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    High-level retrieval interface to embed queries and search stored chunks.
    """

    def __init__(self, embedding_service: EmbeddingService, vector_db: VectorDB) -> None:
        self.embedding_service = embedding_service
        self.vector_db = vector_db

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

        vector_size = len(vectors[0])
        self.vector_db.initialize_collections(company_id, vector_size)
        self.vector_db.insert_chunks(chunks, vectors, metadata_list, company_id)

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
        if filters:
            results = self.vector_db.search_with_filters(query_vector, company_id, chunk_type, filters, top_k)
        else:
            results = self.vector_db.search(query_vector, company_id, chunk_type, top_k)
        return [_format_result(r) for r in results]

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


def _format_result(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = result.get("payload", {})
    return {
        "id": result.get("id"),
        "score": result.get("score"),
        "text": payload.get("text", ""),
        "metadata": {k: v for k, v in payload.items() if k != "text"},
    }
