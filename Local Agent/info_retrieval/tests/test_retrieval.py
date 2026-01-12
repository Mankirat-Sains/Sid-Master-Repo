import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import math

from embeddings.embedding_service import EmbeddingService  # noqa: E402
from retrieval.retriever import Retriever  # noqa: E402
from storage.vector_store import VectorStore, Chunk, SearchResult  # noqa: E402
from ir_utils.config import AppConfig  # noqa: E402


class FakeSupabaseVectorStore(VectorStore):
    def __init__(self) -> None:
        self.records = []

    def upsert(self, chunks):
        self.records.extend(chunks)

    def search(self, query_vector, top_k, filters=None):
        filters = filters or {}
        index_type = filters.get("index_type")
        results = []
        for chunk in self.records:
            meta = chunk.metadata if hasattr(chunk, "metadata") else chunk["metadata"]
            if index_type and meta.get("index_type") != index_type:
                continue
            vec = chunk.embedding if hasattr(chunk, "embedding") else chunk["embedding"]
            score = self._cosine(query_vector, vec)
            results.append(SearchResult(id=meta.get("chunk_id", ""), score=score, text=chunk.text if hasattr(chunk, "text") else chunk["text"], metadata=meta))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def delete_by_artifact(self, artifact_id: str, version_id: str | None = None) -> None:
        self.records = [r for r in self.records if r.metadata.get("artifact_id") != artifact_id]

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0


def test_in_memory_retrieval_round_trip():
    config = AppConfig(
        openai_api_key=None,
        vector_db_path=Path("data/vector_db"),
        metadata_db_path=Path("data/metadata.db"),
        embedding_model="debug-model",
        qdrant_collection="documents",
        use_local_embeddings=False,
        embedding_dim=16,
        log_level="INFO",
    )
    embedding_service = EmbeddingService(config)
    vector_store = FakeSupabaseVectorStore()
    retriever = Retriever(embedding_service, vector_store)

    chunks = [{"text": "The foundation wall is designed for 50 kPa.", "section_title": "Results"}]
    metadata = [
        {
            "chunk_id": "chunk-1",
            "chunk_type": "content",
            "artifact_id": "artifact-1",
            "version_id": "v1",
            "company_id": "acme",
            "section_type": "results",
            "doc_type": "calculation",
        }
    ]

    retriever.index_chunks(chunks, metadata, company_id="acme")
    results = retriever.retrieve_content("foundation", company_id="acme", top_k=1)
    assert results
    assert results[0]["metadata"].get("chunk_type") == "content"
