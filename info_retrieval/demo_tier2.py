"""
Tier 2 Demo: Document generation end-to-end.
Run:
  PYTHONPATH=info_retrieval/src .venv/bin/python -m info_retrieval.demo_tier2 "Draft methodology for structural beam design per ACI 318-19"
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

from embeddings.embedding_service import EmbeddingService
from retrieval.retriever import Retriever
from storage.supabase_vector_store import SupabaseVectorStore
from tier2.drafter import DocumentDrafter
from tier2.template_store import TemplateStore
from utils.config import load_config
from utils.logger import get_logger


def main() -> None:
    load_dotenv()
    logger = get_logger(__name__)

    user_request = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Draft methodology section for structural beam design per ACI 318-19"
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
    print(result["used_template"])
    print("\n=== Citations ===")
    for cite in result["citations"]:
        print(cite)


if __name__ == "__main__":
    main()
