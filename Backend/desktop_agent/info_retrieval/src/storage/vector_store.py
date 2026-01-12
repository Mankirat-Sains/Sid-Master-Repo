from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol


@dataclass
class Chunk:
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: str
    score: float
    text: str
    metadata: Dict[str, object] = field(default_factory=dict)


class VectorStore(Protocol):
    """
    Backend-agnostic interface for vector storage and retrieval.
    """

    def upsert(self, chunks: List[Chunk]) -> None:
        ...

    def search(self, query_vector: List[float], top_k: int, filters: Optional[Dict[str, object]] = None) -> List[SearchResult]:
        ...

    def delete_by_artifact(self, artifact_id: str, version_id: Optional[str] = None) -> None:
        ...
