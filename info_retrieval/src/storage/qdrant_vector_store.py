from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from utils.logger import get_logger
from storage.vector_db import VectorDB
from storage.vector_store import Chunk, SearchResult, VectorStore

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    """
    Adapter to use existing Qdrant-backed VectorDB through the VectorStore interface.
    """

    def __init__(self, vector_db: VectorDB, company_id: str) -> None:
        self.vector_db = vector_db
        self.company_id = company_id

    def upsert(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return
        # group by chunk_type for routing
        grouped: Dict[str, List[Chunk]] = defaultdict(list)
        for chunk in chunks:
            chunk_type = chunk.metadata.get("index_type") or chunk.metadata.get("chunk_type") or "content"
            grouped[str(chunk_type)].append(chunk)

        for chunk_type, group in grouped.items():
            vectors = [c.embedding for c in group]
            chunk_payloads = []
            meta_payloads = []
            for c in group:
                payload = dict(c.metadata)
                payload["text"] = c.text
                payload["chunk_type"] = payload.get("chunk_type") or payload.get("index_type") or chunk_type
                payload["chunk_id"] = payload.get("chunk_id") or c.id
                chunk_payloads.append({"text": c.text, **{k: v for k, v in payload.items() if k != "text"}})
                meta_payloads.append(payload)
            self.vector_db.insert_chunks(chunk_payloads, vectors, meta_payloads, self.company_id)

    def search(self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]] = None) -> List[SearchResult]:
        chunk_type = "content"
        filt = filters or {}
        if "index_type" in filt:
            chunk_type = str(filt.pop("index_type"))
        elif "chunk_type" in filt:
            chunk_type = str(filt.pop("chunk_type"))

        if filt:
            results = self.vector_db.search_with_filters(query_vector, self.company_id, chunk_type, filt, top_k)
        else:
            results = self.vector_db.search(query_vector, self.company_id, chunk_type, top_k)

        return [
            SearchResult(
                id=r.get("id", ""),
                score=float(r.get("score", 0.0)),
                text=r.get("payload", {}).get("text", ""),
                metadata={k: v for k, v in r.get("payload", {}).items() if k != "text"},
            )
            for r in results
        ]

    def delete_by_artifact(self, artifact_id: str, version_id: Optional[str] = None) -> None:
        logger.warning("delete_by_artifact is not implemented for Qdrant adapter.")
