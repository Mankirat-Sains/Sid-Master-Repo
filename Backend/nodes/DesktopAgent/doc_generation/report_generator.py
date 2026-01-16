"""
DOCGEN: Generate a multi-section report via ReportDrafter.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
import json
from typing import Any, Dict

from models.rag_state import RAGState
from config.logging_config import log_query

_DOC_SERVICES: Dict[str, Any] | None = None


def _load_services() -> Dict[str, Any]:
    """Lazy-load Tier2 services (shared with section generation)."""
    global _DOC_SERVICES
    if _DOC_SERVICES is not None:
        return _DOC_SERVICES

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=True)

    from ir_utils.config import load_config
    from embeddings.embedding_service import EmbeddingService
    from retrieval.retriever import Retriever
    from storage.metadata_db import MetadataDB
    from storage.qdrant_vector_store import QdrantVectorStore
    from storage.supabase_vector_store import SupabaseVectorStore
    from storage.vector_db import VectorDB
    from tier2.generator import Tier2Generator
    from tier2.report_drafter import ReportDrafter

    config = load_config()
    embedding_service = EmbeddingService(config)

    try:
        vector_store = SupabaseVectorStore()
        log_query.info("DOCGEN: Using SupabaseVectorStore for report generation.")
    except Exception as exc:  # noqa: BLE001
        log_query.warning(f"DOCGEN: SupabaseVectorStore unavailable, falling back to in-memory Qdrant. ({exc})")
        vector_db = VectorDB(config, use_in_memory=True)
        vector_store = QdrantVectorStore(vector_db, company_id=os.getenv("DEMO_COMPANY_ID", "demo_company"))

    retriever = Retriever(embedding_service, vector_store)
    metadata_db = MetadataDB(config.metadata_db_path)
    generator = Tier2Generator(retriever=retriever, metadata_db=metadata_db)
    drafter = ReportDrafter(generator=generator, metadata_db=metadata_db)

    _DOC_SERVICES = {
        "config": config,
        "embedding_service": embedding_service,
        "vector_store": vector_store,
        "metadata_db": metadata_db,
        "generator": generator,
        "drafter": drafter,
    }
    return _DOC_SERVICES


def _clean_draft_text(text: str) -> str:
    """Remove warning banners and inline citation brackets from report content."""
    if not text:
        return ""
    text = re.sub(r"(?is)\bwarning:\s.*?(?=(\n\n|$))", "", text)
    text = re.sub(r"(?is)\bwarning:\s.*?\.\s*", "", text)
    text = re.sub(r"\[[^\]]*(?:Source|Document|Ref|citation|project|page|source)[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*\d+\s*\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _build_citations_metadata(result: Dict[str, Any], user_request: str | None) -> Dict[str, Any]:
    citations = result.get("citations") or []
    warnings = result.get("warnings") or []
    documents = []
    for cite in citations:
        if not isinstance(cite, dict):
            continue
        documents.append(
            {
                "title": cite.get("title") or cite.get("document_title") or cite.get("filename") or "Source",
                "project": cite.get("project_key") or cite.get("drawing_number") or cite.get("project"),
                "date": cite.get("date") or cite.get("document_date"),
                "author": cite.get("author"),
                "relevance": cite.get("score") or cite.get("similarity") or cite.get("relevance"),
                "content_preview": cite.get("content_preview") or cite.get("preview") or cite.get("text") or "",
                "source_id": cite.get("artifact_id") or cite.get("id") or cite.get("chunk_id") or cite.get("source_id"),
            }
        )

    search_metadata = {
        "original_query": user_request or "",
        "expanded_queries": result.get("expanded_queries") or [],
        "support_score": result.get("support_score") or result.get("support"),
    }

    return {
        "documents": documents,
        "warnings": warnings,
        "search_metadata": search_metadata,
    }


def node_doc_generate_report(state: RAGState) -> dict:
    """Generate a multi-section report draft and stash in state."""
    log_query.info(f"DOCGEN: entered node_doc_generate_report (task_type={state.task_type})")
    try:
        services = _load_services()
        drafter = services["drafter"]
    except Exception as exc:  # noqa: BLE001
        log_query.error(f"DOCGEN: failed to initialize services: {exc}")
        return {
            "doc_generation_result": None,
            "doc_generation_warnings": [f"Doc generation init failed: {exc}"],
        }

    company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")
    overrides: Dict[str, Any] = {}
    if state.doc_request:
        overrides.update({k: v for k, v in state.doc_request.items() if v})
    if state.doc_type:
        overrides["doc_type"] = state.doc_type

    result = drafter.draft_report(
        company_id=company_id,
        user_request=state.user_query or "",
        doc_type=state.doc_type,
        overrides=overrides or None,
    )

    warnings = result.get("warnings", []) or []
    # Mark if any section is TBD/skipped due to missing grounding
    for section in result.get("sections", []):
        if section.get("text", "").strip().startswith("[TBD"):
            warnings.append(f"Section '{section.get('section_type')}' lacks grounding; marked TBD.")

    # Sanitize content and attach metadata for UI presentation
    if isinstance(result.get("draft_text"), str):
        result["draft_text"] = _clean_draft_text(result.get("draft_text"))
    if isinstance(result.get("combined_text"), str):
        result["combined_text"] = _clean_draft_text(result.get("combined_text") or "")
    if isinstance(result.get("sections"), list):
        for section in result["sections"]:
            if isinstance(section, dict):
                for key in ("text", "draft_text", "content", "body"):
                    if isinstance(section.get(key), str):
                        section[key] = _clean_draft_text(section.get(key))

    # Ensure citations metadata is always present for UI consumption
    if not result.get("citations_metadata"):
        result["citations_metadata"] = _build_citations_metadata(result, state.user_query or state.original_question)
    else:
        result["citations_metadata"] = result.get("citations_metadata") or _build_citations_metadata(
            result, state.user_query or state.original_question
        )

    try:
        print(f"🐛 DEBUG: doc_generation_result keys: {list(result.keys())}")
        print(f"🐛 DEBUG: Has citations_metadata? {'citations_metadata' in result}")
        if "citations_metadata" in result:
            print(f"🐛 DEBUG: citations_metadata: {json.dumps(result['citations_metadata'], indent=2)}")
        else:
            print("🐛 DEBUG: citations_metadata NOT FOUND - need to create it!")
    except Exception as exc:  # noqa: BLE001
        log_query.warning(f"DOCGEN: failed to log citations_metadata debug info ({exc})")

    return {
        "doc_generation_result": result,
        "doc_generation_warnings": warnings,
    }
