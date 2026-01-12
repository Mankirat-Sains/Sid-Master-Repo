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
from supabase import create_client
from openai import OpenAI

from embeddings.embedding_service import EmbeddingService
from retrieval.retriever import Retriever
from storage.supabase_vector_store import SupabaseVectorStore
from tier2.drafter import DocumentDrafter
from tier2.template_store import TemplateStore
from ir_utils.config import load_config
from ir_utils.logger import get_logger


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
        sys.argv[1] if len(sys.argv) > 1 else "Draft methodology section for structural beam design per ACI 318-19"
    )

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY/ANON_KEY are required.")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is required for generation.")

    company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")

    # Initialize dependencies
    config = load_config()
    embedding_service = EmbeddingService(config)
    vector_store = SupabaseVectorStore()
    retriever = Retriever(embedding_service, vector_store)
    supabase_client = create_client(supabase_url, supabase_key)
    template_store = TemplateStore(supabase_client)
    llm_client = OpenAI(api_key=openai_key)

    drafter = DocumentDrafter(template_store, retriever, llm_client)

    logger.info("Drafting section for request: %s", user_request)
    result = drafter.draft_section(company_id=company_id, user_request=user_request)

    print("\n=== Drafted Text ===\n")
    print(result["draft_text"])
    print("\n=== Used Template ===")
    print(result.get("used_template"))
    print("\n=== Citations ===")
    for cite in result["citations"]:
        print(cite)

    output_path = os.getenv("DRAFT_OUTPUT_CSV", "./data/drafted_sections.csv")
    _append_output_csv(output_path, user_request, result)
    logger.info("Draft saved to %s (length=%s chars)", output_path, len(result.get("draft_text", "")))


if __name__ == "__main__":
    main()
