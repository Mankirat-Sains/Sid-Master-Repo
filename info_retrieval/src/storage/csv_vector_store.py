"""
CSV-backed VectorStore for test-only usage.
Stores id, text, embedding, and metadata rows in a flat file for simple debugging.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from storage.vector_store import Chunk, SearchResult, VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)


class CSVVectorStore(VectorStore):
    """
    Lightweight VectorStore that persists to a CSV file.
    Suitable for local tests only (no concurrency or locking).
    """

    def __init__(self, path: str | Path = "data/vector_store.csv") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def upsert(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return
        rows = {row["id"]: row for row in self._read_rows()}
        for chunk in chunks:
            rows[chunk.id] = {
                "id": chunk.id,
                "text": chunk.text,
                "embedding": chunk.embedding,
                "metadata": dict(chunk.metadata),
            }
        self._write_rows(list(rows.values()))

    def search(self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]] = None) -> List[SearchResult]:
        filters = filters or {}
        results: List[SearchResult] = []
        for row in self._read_rows():
            metadata = row["metadata"]
            if not self._matches_filters(metadata, filters):
                continue
            score = self._cosine(query_vector, row["embedding"])
            results.append(SearchResult(id=row["id"], score=score, text=row["text"], metadata=metadata))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def delete_by_artifact(self, artifact_id: str, version_id: Optional[str] = None) -> None:
        kept = []
        for row in self._read_rows():
            meta = row["metadata"]
            if meta.get("artifact_id") != artifact_id:
                kept.append(row)
                continue
            if version_id and meta.get("version_id") != version_id:
                kept.append(row)
        self._write_rows(kept)

    def _read_rows(self) -> List[Dict[str, object]]:
        if not self.path.exists():
            return []
        rows: List[Dict[str, object]] = []
        try:
            with self.path.open("r", newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    rows.append(
                        {
                            "id": row["id"],
                            "text": row.get("text", ""),
                            "embedding": json.loads(row.get("embedding", "[]")),
                            "metadata": json.loads(row.get("metadata", "{}")),
                        }
                    )
        except Exception as exc:
            logger.error("Failed to read CSV vector store: %s", exc)
        return rows

    def _write_rows(self, rows: List[Dict[str, object]]) -> None:
        fieldnames = ["id", "text", "embedding", "metadata"]
        with self.path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "id": row["id"],
                        "text": row.get("text", ""),
                        "embedding": json.dumps(row.get("embedding", [])),
                        "metadata": json.dumps(row.get("metadata", {})),
                    }
                )

    def _matches_filters(self, metadata: Dict[str, object], filters: Dict[str, object]) -> bool:
        for key, value in filters.items():
            if value is None:
                continue
            if metadata.get(key) != value:
                return False
        return True

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
