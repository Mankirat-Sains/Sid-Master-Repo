"""
End-to-end demo of Tier 1 ingestion and retrieval.
Run: python -m info_retrieval.demo
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from embeddings.embedding_service import EmbeddingService  # noqa: E402
from ingest.pipeline import IngestionPipeline  # noqa: E402
from retrieval.retriever import Retriever  # noqa: E402
from storage.metadata_db import MetadataDB  # noqa: E402
from storage.qdrant_vector_store import QdrantVectorStore  # noqa: E402
from storage.vector_db import VectorDB  # noqa: E402
from utils.config import load_config  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    load_dotenv()
    config = load_config()
    company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")

    embedding_service = EmbeddingService(config)
    vector_db = VectorDB(config, use_in_memory=False)
    vector_store = QdrantVectorStore(vector_db, company_id=company_id)
    metadata_db = MetadataDB(config.metadata_db_path)

    pipeline = IngestionPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        metadata_db=metadata_db,
        company_id=company_id,
    )

    sample_doc = Path("info_retrieval/data/sample_docs/thermal_calculation.docx")
    if not sample_doc.exists():
        logger.error("Sample doc missing at %s", sample_doc)
        return

    result = pipeline.ingest(str(sample_doc))
    logger.info("Ingestion result: %s", result)

    retriever = Retriever(embedding_service, vector_store)
    content = retriever.retrieve_content("thermal analysis methodology", company_id=company_id, top_k=3)
    style = retriever.retrieve_style_examples("methodology", company_id=company_id, top_k=2)

    print("\nContent Results:")
    for idx, item in enumerate(content, 1):
        print(f"{idx}. score={item['score']:.3f} section={item['metadata'].get('section_type')} text={item['text'][:120]}...")

    print("\nStyle Examples:")
    for idx, item in enumerate(style, 1):
        print(f"{idx}. score={item['score']:.3f} text={item['text'][:140]}...")


if __name__ == "__main__":
    main()
