import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from embeddings.embedding_service import EmbeddingService  # noqa: E402
from retrieval.retriever import Retriever  # noqa: E402
from storage.vector_db import VectorDB  # noqa: E402
from utils.config import AppConfig  # noqa: E402


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
    vector_db = VectorDB(config, use_in_memory=True)
    retriever = Retriever(embedding_service, vector_db)

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
