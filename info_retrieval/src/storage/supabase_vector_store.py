from __future__ import annotations

import os
import uuid
import re
from typing import Dict, List, Optional

from utils.logger import get_logger
from storage.vector_store import Chunk, SearchResult, VectorStore

logger = get_logger(__name__)

try:
    from supabase import create_client  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    create_client = None
try:
    from postgrest.exceptions import APIError  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    APIError = Exception


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
        self.id_column = os.getenv("SUPABASE_ID_COLUMN", "id")
        self.content_column = os.getenv("SUPABASE_CONTENT_COLUMN", "content")
        self.metadata_column = os.getenv("SUPABASE_METADATA_COLUMN", "metadata")
        self.embedding_column = os.getenv("SUPABASE_EMBEDDING_COLUMN", "embedding")
        self.passthrough_columns = self._parse_passthrough_columns(
            os.getenv(
                "SUPABASE_PASSTHROUGH_COLUMNS",
                "artifact_id,version_id,company_id,chunk_type,index_type,section_type,doc_type,source,file_path,heading,page_number",
            )
        )
        self._metadata_supported = bool(self.metadata_column)

    def upsert(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return
        max_attempts = len(self.passthrough_columns) + 2  # include metadata retry
        attempt = 0
        while attempt < max_attempts:
            rows = [self._build_row(c, include_metadata=self._metadata_supported) for c in chunks]
            try:
                self.client.table(self.table).upsert(rows).execute()
                return
            except APIError as exc:
                msg = str(exc)
                lower_msg = msg.lower()
                if self._metadata_supported and "metadata" in lower_msg:
                    logger.warning("Supabase table missing metadata column; retrying without metadata.")
                    self._metadata_supported = False
                    attempt += 1
                    continue
                missing_col = self._extract_missing_column(msg)
                if missing_col and missing_col in self.passthrough_columns:
                    logger.warning("Supabase table missing column '%s'; retrying without it.", missing_col)
                    self.passthrough_columns = [c for c in self.passthrough_columns if c != missing_col]
                    attempt += 1
                    continue
                logger.error("Supabase upsert failed: %s", exc)
                raise
            except Exception as exc:
                logger.error("Supabase upsert failed: %s", exc)
                raise

    def search(self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]] = None) -> List[SearchResult]:
        payloads = self._build_search_payloads(query_vector, top_k, filters)
        data: List[Dict[str, object]] = []
        last_exc: Exception | None = None

        for payload in payloads:
            try:
                resp = self.client.rpc(self.rpc_function, payload).execute()
                data = resp.data or []
                break
            except APIError as exc:
                last_exc = exc
                logger.warning("Supabase RPC search failed with payload keys %s: %s", sorted(payload.keys()), exc)
            except Exception as exc:
                logger.error("Supabase RPC search failed: %s", exc)
                raise

        if last_exc and not data:
            raise last_exc

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

    def _build_row(self, chunk: Chunk, include_metadata: bool = True) -> Dict[str, object]:
        metadata = dict(chunk.metadata)
        chunk_id = str(metadata.get("chunk_id") or chunk.id)
        metadata["chunk_id"] = chunk_id
        metadata["chunk_type"] = metadata.get("chunk_type") or metadata.get("index_type") or "content"
        metadata.pop("text", None)
        metadata.pop("embedding", None)

        row: Dict[str, object] = {
            self.id_column: self._coerce_uuid(chunk_id),
            self.content_column: chunk.text,
            self.embedding_column: chunk.embedding,
        }
        for col in self.passthrough_columns:
            if col == "chunk_type":
                row[col] = metadata.get("chunk_type")
                continue
            if col == "index_type":
                row[col] = metadata.get("chunk_type") or metadata.get("index_type")
                continue
            if col in metadata:
                row[col] = metadata[col]
        if include_metadata and self.metadata_column:
            row[self.metadata_column] = metadata
        return row

    def _coerce_uuid(self, candidate: str) -> str:
        """
        Ensure ID is valid for uuid-typed columns; generate deterministic UUID when needed.
        """
        try:
            return str(uuid.UUID(candidate))
        except Exception:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, candidate))

    def _parse_passthrough_columns(self, raw: str) -> List[str]:
        return [c.strip() for c in raw.split(",") if c.strip()]

    def _extract_missing_column(self, message: str) -> Optional[str]:
        patterns = [
            r"Could not find the '([^']+)' column",
            r"column \"([^\"]+)\" does not exist",
            r"column '([^']+)' does not exist",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _build_search_payloads(
        self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        base = {"query_embedding": query_vector, "match_count": top_k}
        if not filters:
            return [base]

        mapped_filters = self._map_filters_for_rpc(filters)
        payloads = [{**base, **mapped_filters}]

        legacy_filters = {k: v for k, v in (filters or {}).items() if v is not None}
        if legacy_filters and legacy_filters.keys() != mapped_filters.keys():
            payloads.append({**base, **legacy_filters})
        return payloads

    def _map_filters_for_rpc(self, filters: Dict[str, object]) -> Dict[str, object]:
        """
        Align filter keys with Supabase RPC signature (e.g., `company_filter` instead of `company_id`).
        """
        key_map = {
            "artifact_id": "artifact_filter",
            "artifact_filter": "artifact_filter",
            "chunk_type": "index_type_filter",
            "company_id": "company_filter",
            "company_filter": "company_filter",
            "doc_type": "doc_type_filter",
            "doc_type_filter": "doc_type_filter",
            "index_type": "index_type_filter",
            "index_type_filter": "index_type_filter",
            "section_type": "section_type_filter",
            "section_type_filter": "section_type_filter",
            "version_id": "version_filter",
            "version_filter": "version_filter",
        }

        mapped: Dict[str, object] = {}
        for key, value in filters.items():
            if value is None:
                continue
            if key in key_map:
                mapped[key_map[key]] = value
            elif key.endswith("_filter"):
                mapped[key] = value
            else:
                logger.debug("Ignoring unsupported filter key '%s' for Supabase RPC.", key)
        return mapped
