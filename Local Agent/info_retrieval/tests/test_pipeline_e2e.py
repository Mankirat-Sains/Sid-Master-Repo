import sys
from pathlib import Path
import math

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from embeddings.embedding_service import EmbeddingService  # noqa: E402
from ingest.pipeline import IngestionPipeline  # noqa: E402
from storage.metadata_db import MetadataDB  # noqa: E402
from storage.vector_store import Chunk, SearchResult, VectorStore  # noqa: E402
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
            meta = chunk.metadata
            if index_type and meta.get("index_type") != index_type:
                continue
            score = self._cosine(query_vector, chunk.embedding)
            results.append(SearchResult(id=meta.get("chunk_id", ""), score=score, text=chunk.text, metadata=meta))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def delete_by_artifact(self, artifact_id: str, version_id: str | None = None) -> None:
        self.records = [r for r in self.records if r.metadata.get("artifact_id") != artifact_id]

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0


def test_ingestion_pipeline_end_to_end(tmp_path):
    base = Path(__file__).resolve().parents[1] / "data" / "sample_docs"
    docx_path = base / "thermal_calculation.docx"
    if not docx_path.exists():
        return

    config = AppConfig(
        openai_api_key=None,
        vector_db_path=Path("data/vector_db"),
        metadata_db_path=tmp_path / "metadata.db",
        embedding_model="debug-model",
        qdrant_collection="documents",
        use_local_embeddings=False,
        embedding_dim=32,
        log_level="INFO",
    )
    embedding_service = EmbeddingService(config)
    vector_store = FakeSupabaseVectorStore()
    metadata_db = MetadataDB(config.metadata_db_path)

    pipeline = IngestionPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        metadata_db=metadata_db,
        company_id="acme",
    )

    result = pipeline.ingest(str(docx_path))
    assert result["chunk_count"] > 0
    assert result["content_chunks"] >= 1

    # Verify retrieval through fake store
    retriever_embedding = embedding_service.embed_text("thermal analysis")
    matches = vector_store.search(retriever_embedding, top_k=3, filters={"index_type": "content"})
    assert matches
