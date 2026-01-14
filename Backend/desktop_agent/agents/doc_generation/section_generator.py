"""
DOCGEN: Generate a single section via Tier2Generator.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict

from models.rag_state import RAGState
from config.logging_config import log_query

_DOC_SERVICES: Dict[str, Any] | None = None


def _load_services() -> Dict[str, Any]:
    """Lazy-load Tier2 services (config, generator, metadata)."""
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
    log_query.info(
        "DOCGEN: entered node_doc_generate_section | task_type=%s | doc_type=%s | section_type=%s | doc_request=%s",
        state.task_type,
        state.doc_type,
        state.section_type,
        state.doc_request,
    )
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

    def _draft_with_overrides(extra: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(overrides)
        for key, val in extra.items():
            if val is None:
                merged.pop(key, None)
            else:
                merged[key] = val
        log_query.info("DOCGEN: calling generator with overrides=%s", {k: merged[k] for k in merged})
        return generator.draft_section(
            company_id=company_id,
            user_request=state.user_query or "",
            overrides=merged or None,
        )

    result = _draft_with_overrides({})

    warnings = result.get("warnings", []) or []
    draft_text = result.get("draft_text", "") or ""
    debug = result.get("debug", {}) or {}
    if draft_text.strip().startswith("[TBD") or debug.get("content_chunks_used", 1) == 0:
        warnings.append("No grounding content for this section; draft is template-like or TBD.")

    # If we failed to ground (no citations) try a relaxed pass without doc/section filters
    citations = result.get("citations") or []
    if not citations:
        log_query.info("DOCGEN: no citations found; retrying without doc_type/section_type filters")
        relaxed_result = _draft_with_overrides({"doc_type": None, "section_type": None})
        relaxed_citations = relaxed_result.get("citations") or []
        if relaxed_citations:
            result = relaxed_result
            warnings = relaxed_result.get("warnings", []) or warnings
            draft_text = relaxed_result.get("draft_text", draft_text)

    # Diagnostics: log which sources were used
    cite_sources = []
    for cite in result.get("citations") or []:
        cite_sources.append(
            {
                "artifact_id": cite.get("artifact_id"),
                "chunk_id": cite.get("chunk_id"),
                "score": cite.get("score"),
            }
        )
    log_query.info("DOCGEN: citations used=%s", cite_sources)

    return {
        "doc_generation_result": result,
        "doc_generation_warnings": warnings,
    }


class SectionGenerator:
    """
    Lightweight wrapper to mirror the legacy docgen interface expected by deep agent tools.
    Provides a .generate(doc_request, context_path, output_dir) method.
    """

    def __init__(self) -> None:
        self._services: Dict[str, Any] | None = None

    def _get_generator(self):
        if self._services is None:
            self._services = _load_services()
        return self._services["generator"]

    def generate(self, doc_request: Dict[str, Any], context_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Generate a document section, using context file when available.

        Args:
            doc_request: Dictionary of doc generation parameters.
            context_path: Path to a JSON context file (optional).
            output_dir: Directory for any outputs (kept for parity; not used directly here).
        """
        try:
            ctx = {}
            if context_path and Path(context_path).exists():
                try:
                    ctx = json.loads(Path(context_path).read_text())
                except Exception:
                    pass

            user_request = ""
            if doc_request:
                user_request = doc_request.get("user_query") or doc_request.get("title") or ""
            if not user_request and isinstance(ctx, dict):
                user_request = (
                    ctx.get("doc_request", {}).get("title")
                    or ctx.get("user_context", {}).get("user_query")
                    or ""
                )

            overrides: Dict[str, Any] = {}
            if doc_request:
                overrides.update({k: v for k, v in doc_request.items() if v is not None})

            generator = self._get_generator()
            company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")
            result = generator.draft_section(
                company_id=company_id,
                user_request=user_request,
                overrides=overrides or None,
            )
            result = result or {}
            # Ensure a metadata block is always present
            metadata = result.get("metadata") or {}
            metadata["used_context_file"] = bool(context_path and Path(context_path).exists())
            result["metadata"] = metadata
            return result
        except Exception as exc:  # pragma: no cover - defensive fallback
            log_query.error(f"DOCGEN: SectionGenerator.generate failed: {exc}")
            return {
                "draft_text": f"# Document\n\nGenerated content for: {doc_request.get('title', 'Untitled') if doc_request else 'Untitled'}",
                "sections": [],
                "warnings": [f"SectionGenerator fallback used: {exc}"],
                "metadata": {"fallback": True, "reason": str(exc)},
            }
