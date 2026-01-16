from __future__ import annotations

from typing import Dict, Optional, Any

from ir_utils.logger import get_logger

logger = get_logger(__name__)

try:
    from supabase import create_client  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    create_client = None


def resolve_template_sections(
    company_id: str,
    doc_type: str,
    url: Optional[str] = None,
    key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch template_id, template metadata, and section_id mapping from Supabase
    `document_templates` and `template_sections`.
    Returns None if Supabase client is unavailable or no template found.
    """
    if create_client is None:
        logger.warning("Supabase client not available; skipping template resolution.")
        return None

    url = url or import_env("SUPABASE_URL")
    key = key or import_env("SUPABASE_SERVICE_KEY") or import_env("SUPABASE_KEY") or import_env("SUPABASE_ANON_KEY")
    if not url or not key:
        logger.warning("Supabase credentials missing; skipping template resolution.")
        return None

    client = create_client(url, key)
    try:
        tmpl_resp = (
            client.table("document_templates")
            .select("template_id, doc_type, company_id, template_name, version, metadata")
            .eq("company_id", company_id)
            .eq("doc_type", doc_type)
            .eq("is_active", True)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        templates = tmpl_resp.data or []
        if not templates:
            logger.info("No active template found for company=%s doc_type=%s", company_id, doc_type)
            return None
        template_id = templates[0]["template_id"]
        template_metadata = templates[0].get("metadata") or {}
        template_name = templates[0].get("template_name")
        template_version = templates[0].get("version")

        sections_resp = (
            client.table("template_sections")
            .select("section_id, section_type, section_name, position_order")
            .eq("template_id", template_id)
            .order("position_order")
            .execute()
        )
        sections = sections_resp.data or []
        section_id_map = {s["section_type"]: s["section_id"] for s in sections if s.get("section_type") and s.get("section_id")}

        return {
            "template_id": template_id,
            "template_metadata": template_metadata,
            "template_name": template_name,
            "template_version": template_version,
            "sections": sections,
            "section_id_map": section_id_map,
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Template resolution failed for company=%s doc_type=%s: %s", company_id, doc_type, exc)
        return None


def import_env(name: str) -> Optional[str]:
    import os

    return os.getenv(name)
