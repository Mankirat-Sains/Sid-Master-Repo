"""
DOCGEN: Generate a multi-section report via ReportDrafter.
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
    here = Path(__file__).resolve()
    candidates = set()
    if len(here.parents) >= 3:
        candidates.add(here.parents[3])
    if len(here.parents) >= 2:
        candidates.add(here.parents[2])
    if len(here.parents) >= 4:
        candidates.add(here.parents[4])
    candidates.add((here.parent / "../../../info_retrieval/src").resolve())

    for base in candidates:
        ir_src = Path(base) / "info_retrieval" / "src"
        if ir_src.exists() and str(ir_src) not in sys.path:
            sys.path.insert(0, str(ir_src))


def _load_services() -> Dict[str, Any]:
    """Lazy-load Tier2 services (shared with section generation)."""
    global _DOC_SERVICES
    if _DOC_SERVICES is not None:
        return _DOC_SERVICES

    _ensure_info_retrieval_path()
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

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

    return {
        "doc_generation_result": result,
        "doc_generation_warnings": warnings,
    }
