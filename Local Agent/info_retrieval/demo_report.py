"""
Demo: draft a full report by generating multiple sections using Tier 2.
"""
from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from embeddings.embedding_service import EmbeddingService
from retrieval.retriever import Retriever
from storage.metadata_db import MetadataDB
from storage.qdrant_vector_store import QdrantVectorStore
from storage.supabase_vector_store import SupabaseVectorStore
from storage.vector_db import VectorDB
from tier2.generator import Tier2Generator
from tier2.report_drafter import ReportDrafter
from ir_utils.config import load_config
from ir_utils.logger import get_logger


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft a full report (multi-section) using Tier 2.")
    parser.add_argument("prompt", nargs="?", default="Draft a RP for PT Investigation and 5 Year Plan", help="User request/prompt")
    parser.add_argument("--company", default=None, help="Company ID (default from DEMO_COMPANY_ID or demo_company)")
    parser.add_argument("--doc_type", default=None, help="Doc type (e.g., design_report)")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    logger = get_logger(__name__)
    args = build_args()

    config = load_config()
    company_id = args.company or os.getenv("DEMO_COMPANY_ID", "demo_company")

    embedding_service = EmbeddingService(config)
    try:
        vector_store = SupabaseVectorStore()
        logger.info("Using SupabaseVectorStore.")
    except Exception as exc:
        logger.warning("Supabase unavailable (%s); falling back to in-memory Qdrant.", exc)
        vector_db = VectorDB(config, use_in_memory=True)
        vector_store = QdrantVectorStore(vector_db, company_id=company_id)

    retriever = Retriever(embedding_service, vector_store)
    metadata_db = MetadataDB(config.metadata_db_path)
    generator = Tier2Generator(retriever=retriever, metadata_db=metadata_db)
    report_drafter = ReportDrafter(generator=generator, metadata_db=metadata_db)

    result = report_drafter.draft_report(
        company_id=company_id,
        user_request=args.prompt,
        doc_type=args.doc_type,
    )

    section_order = result.get("section_order", [])
    section_source = result.get("meta", {}).get("section_source")
    print("Section order:", ", ".join(section_order))
    if section_source:
        print(f"Section source: {section_source}")

    print("\n=== Combined Report ===\n")
    print(result["combined_text"])
    print("\n=== Section summaries ===")
    for section in result["sections"]:
        print(f"- {section['section_type']}: {len(section.get('text',''))} chars, citations={len(section.get('citations', []))}")

    print("\n=== Section debug ===")
    for section in result.get("section_status", []):
        dbg = section.get("debug", {}) or {}
        print(
            f"- {section['section_type']}: {section.get('status')} | "
            f"content_chunks={dbg.get('content_chunks_used', 0)} ({dbg.get('content_source','?')}) | "
            f"style_chunks={dbg.get('style_chunks_used', 0)} ({dbg.get('style_source','?')})"
        )

    generated_sections = [s for s in result.get("sections", []) if s.get("section_type") in {"methodology", "recommendations"}]
    if generated_sections:
        sample = generated_sections[0]
        print("\n=== Sample section ===")
        print(f"{sample['section_type'].title()}:\n{sample.get('text','')}")

    if result.get("warnings"):
        print("\nWarnings:")
        for w in result["warnings"]:
            print(f"- {w}")


if __name__ == "__main__":
    main()
