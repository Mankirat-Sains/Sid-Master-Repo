"""
Tier 2 Demo: Document generation end-to-end.
Run:
  PYTHONPATH=info_retrieval/src .venv/bin/python -m info_retrieval.demo_tier2 "Draft methodology for structural beam design per ACI 318-19"
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from embeddings.embedding_service import EmbeddingService
from retrieval.retriever import Retriever
from storage.qdrant_vector_store import QdrantVectorStore
from storage.supabase_vector_store import SupabaseVectorStore
from storage.vector_db import VectorDB
from storage.metadata_db import MetadataDB
from tier2.generator import Tier2Generator
from utils.config import load_config
from utils.logger import get_logger


def _append_output_csv(path: str, user_request: str, result: dict) -> None:
    """
    Append the drafted output to a CSV so the user can inspect generation results.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "timestamp",
        "request",
        "doc_type",
        "section_type",
        "min_chars",
        "max_chars",
        "length_actual",
        "draft_text",
        "citations_json",
    ]
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        length_target = result.get("length_target", {}) or {}
        writer.writerow(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "request": user_request,
                "doc_type": result.get("doc_type"),
                "section_type": result.get("section_type"),
                "min_chars": length_target.get("min_chars"),
                "max_chars": length_target.get("max_chars"),
                "length_actual": len(result.get("draft_text", "")),
                "draft_text": result.get("draft_text"),
                "citations_json": json.dumps(result.get("citations", [])),
            }
        )


def main() -> None:
    load_dotenv()
    logger = get_logger(__name__)

    user_request = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Draft methodology section for structural design report"
    )

    config = load_config()
    company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")

    embedding_service = EmbeddingService(config)
    vector_store = None
    try:
        vector_store = SupabaseVectorStore()
        logger.info("Using SupabaseVectorStore.")
    except Exception as exc:
        logger.warning("SupabaseVectorStore unavailable (%s); using in-memory Qdrant fallback.", exc)
        vector_db = VectorDB(config, use_in_memory=True)
        vector_store = QdrantVectorStore(vector_db, company_id=company_id)

    retriever = Retriever(embedding_service, vector_store)
    metadata_db = MetadataDB(config.metadata_db_path)
    generator = Tier2Generator(retriever=retriever, metadata_db=metadata_db)

    logger.info("Drafting section for request: %s", user_request)
    result = generator.draft_section(company_id=company_id, user_request=user_request)

    print("\n=== Drafted Text ===\n")
    print(result["draft_text"])
    print("\n=== Citations ===")
    for cite in result["citations"]:
        print(cite)

    output_path = os.getenv("DRAFT_OUTPUT_CSV", "./data/drafted_sections.csv")
    _append_output_csv(output_path, user_request, result)
    logger.info("Draft saved to %s (length=%s chars)", output_path, len(result.get("draft_text", "")))


if __name__ == "__main__":
    main()
