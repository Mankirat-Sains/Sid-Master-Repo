from __future__ import annotations

import os
from typing import Dict, List, Optional

from ..utils.logger import get_logger
from .vector_store import Chunk, SearchResult, VectorStore

logger = get_logger(__name__)

try:
    from supabase import create_client  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    create_client = None


class SupabaseVectorStore(VectorStore):
    """
    Supabase-backed vector store using RPC or table upsert.
    Expects a table name for vectors and an RPC for similarity search.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        table: Optional[str] = None,
        rpc_function: Optional[str] = None,
    ) -> None:
        if create_client is None:
            raise ImportError("supabase-py is required for SupabaseVectorStore")
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not self.url or not self.key:
            raise ValueError("Supabase URL/KEY missing.")
        self.client = create_client(self.url, self.key)
        self.table = table or os.getenv("SUPABASE_CHUNK_TABLE", "chunks")
        self.rpc_function = rpc_function or os.getenv("SUPABASE_MATCH_RPC", "match_chunks")

    def upsert(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return
        rows = []
        for c in chunks:
            meta = dict(c.metadata)
            meta["text"] = c.text
            meta["chunk_id"] = meta.get("chunk_id") or c.id
            rows.append(meta)
        try:
            self.client.table(self.table).upsert(rows).execute()
        except Exception as exc:
            logger.error("Supabase upsert failed: %s", exc)
            raise

    def search(self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]] = None) -> List[SearchResult]:
        payload = {
            "query_embedding": query_vector,
            "match_count": top_k,
        }
        if filters:
            payload.update(filters)
        try:
            resp = self.client.rpc(self.rpc_function, payload).execute()
            data = resp.data or []
        except Exception as exc:
            logger.error("Supabase RPC search failed: %s", exc)
            raise

        results: List[SearchResult] = []
        for row in data:
            metadata = row.get("metadata") or row.get("payload") or {}
            text = row.get("content") or metadata.get("text", "")
            score = row.get("similarity") or row.get("score") or 0.0
            results.append(
                SearchResult(
                    id=str(row.get("id", metadata.get("chunk_id", ""))),
                    score=float(score),
                    text=text,
                    metadata=metadata,
                )
            )
        return results

    def delete_by_artifact(self, artifact_id: str, version_id: Optional[str] = None) -> None:
        query = self.client.table(self.table).delete().eq("artifact_id", artifact_id)
        if version_id:
            query = query.eq("version_id", version_id)
        query.execute()
