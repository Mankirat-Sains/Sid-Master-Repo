"""
DOCGEN: Generate a single section via Tier2Generator.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

from models.rag_state import RAGState
from config.logging_config import log_query

_DOC_SERVICES: Dict[str, Any] | None = None


def _ensure_info_retrieval_path() -> None:
    root = Path(__file__).resolve().parents[3]
    ir_src = root / "info_retrieval" / "src"
    if ir_src.exists() and str(ir_src) not in sys.path:
        sys.path.append(str(ir_src))


def _load_services() -> Dict[str, Any]:
    """Lazy-load Tier2 services (config, generator, metadata)."""
    global _DOC_SERVICES
    if _DOC_SERVICES is not None:
        return _DOC_SERVICES

    _ensure_info_retrieval_path()
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

    from utils.config import load_config
    from embeddings.embedding_service import EmbeddingService
    from retrieval.retriever import Retriever
    from storage.metadata_db import MetadataDB
    from storage.qdrant_vector_store import QdrantVectorStore
    from storage.supabase_vector_store import SupabaseVectorStore
    from storage.vector_db import VectorDB
    from tier2.generator import Tier2Generator

    config = load_config()
    embedding_service = EmbeddingService(config)

    try:
        vector_store = SupabaseVectorStore()
        log_query.info("DOCGEN: Using SupabaseVectorStore for generation.")
    except Exception as exc:  # noqa: BLE001
        log_query.warning(f"DOCGEN: SupabaseVectorStore unavailable, falling back to in-memory Qdrant. ({exc})")
        vector_db = VectorDB(config, use_in_memory=True)
        vector_store = QdrantVectorStore(vector_db, company_id=os.getenv("DEMO_COMPANY_ID", "demo_company"))

    retriever = Retriever(embedding_service, vector_store)
    metadata_db = MetadataDB(config.metadata_db_path)
    generator = Tier2Generator(retriever=retriever, metadata_db=metadata_db)

    _DOC_SERVICES = {
        "config": config,
        "embedding_service": embedding_service,
        "vector_store": vector_store,
        "metadata_db": metadata_db,
        "generator": generator,
    }
    return _DOC_SERVICES


def node_doc_generate_section(state: RAGState) -> dict:
    """Generate a section draft and stash in state."""
    log_query.info(f"DOCGEN: entered node_doc_generate_section (task_type={state.task_type})")
    try:
        services = _load_services()
        generator = services["generator"]
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
    if state.section_type:
        overrides["section_type"] = state.section_type

    result = generator.draft_section(
        company_id=company_id,
        user_request=state.user_query or "",
        overrides=overrides or None,
    )

    warnings = result.get("warnings", []) or []
    draft_text = result.get("draft_text", "") or ""
    debug = result.get("debug", {}) or {}
    if draft_text.strip().startswith("[TBD") or debug.get("content_chunks_used", 1) == 0:
        warnings.append("No grounding content for this section; draft is template-like or TBD.")

    return {
        "doc_generation_result": result,
        "doc_generation_warnings": warnings,
    }
