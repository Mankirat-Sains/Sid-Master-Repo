from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from tier2.generator import Tier2Generator
from config.settings import SECTION_BY_SECTION_GENERATION, SECTION_BY_SECTION_ALLOWLIST
import os
import requests
from ir_utils.logger import get_logger

logger = get_logger(__name__)

# Default ordering when we cannot infer/template
CORE_REPORT_SECTIONS = [
    "executive_summary",
    "background",
    "detailed_analysis",
    "recommendations",
    "conclusion",
]
DEFAULT_SECTION_ORDER = CORE_REPORT_SECTIONS + [
    "scope",
    "methodology",
    "findings",
    "results",
    "limitations",
    "appendix",
]
SAFETY_FALLBACK_SECTIONS = CORE_REPORT_SECTIONS
MIN_INFERRED_SECTIONS = 4

DISPLAY_LABELS = {
    "executive_summary": "Executive Summary",
    "background": "Background",
    "introduction": "Background",
    "scope": "Background and Scope",
    "methodology": "Methodology",
    "analysis": "Detailed Analysis",
    "findings": "Detailed Analysis",
    "results": "Detailed Analysis",
    "detailed_analysis": "Detailed Analysis",
    "recommendations": "Recommendations",
    "limitations": "Limitations",
    "conclusion": "Conclusion",
}


def preferred_sort(section_types: List[str]) -> List[str]:
    order_map = {name: idx for idx, name in enumerate(DEFAULT_SECTION_ORDER)}
    return sorted(section_types, key=lambda s: order_map.get(s, len(DEFAULT_SECTION_ORDER) + 1))


class ReportDrafter:
    """
    Orchestrates multi-section report generation using the existing Tier2Generator.
    """

    def __init__(self, generator: Tier2Generator, metadata_db) -> None:
        self.generator = generator
        self.metadata_db = metadata_db

    def draft_report(
        self,
        company_id: str,
        user_request: str,
        doc_type: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        overrides = overrides or {}
        doc_type = overrides.get("doc_type") or doc_type or self._infer_doc_type(user_request) or "design_report"
        template_id = overrides.get("template_id")
        doc_type_variant = overrides.get("doc_type_variant")
        section_queue_override = overrides.get("section_queue") or []
        template_sections_override = overrides.get("template_sections") or []
        section_order: List[str] = []
        source = "default"
        resolved_template_id: Optional[str] = None
        if section_queue_override:
            section_order = [sec.get("section_type") for sec in section_queue_override if isinstance(sec, dict) and sec.get("section_type")]
            source = "planner_queue"
            resolved_template_id = template_id or overrides.get("template_id")
        elif template_sections_override:
            section_order = [
                sec.get("section_type") for sec in template_sections_override if isinstance(sec, dict) and sec.get("section_type")
            ]
            source = "planner_template_sections"
            resolved_template_id = template_id or overrides.get("template_id")
        else:
            section_order, source, resolved_template_id = self.get_section_order(company_id, doc_type)
        template_id = template_id or resolved_template_id
        section_order = self._ensure_core_sections(section_order)

        sections_output: List[Dict[str, Any]] = []
        section_status: List[Dict[str, Any]] = []
        warnings: List[str] = []
        rolling_approved: List[Dict[str, Any]] = list(overrides.get("approved_sections") or [])

        for section_type in section_order:
            section_overrides = {
                **(overrides or {}),
                "doc_type": doc_type,
                "section_type": section_type,
                "template_id": template_id,
                "doc_type_variant": doc_type_variant,
                "approved_sections": rolling_approved,
            }
            result = self.generator.draft_section(
                company_id=company_id,
                user_request=user_request,
                overrides=section_overrides,
            )
            section_warnings = result.get("warnings", [])
            if result.get("draft_text", "").startswith("[TBD"):
                warnings.extend(section_warnings or [])
                warnings.append(f"Section '{section_type}' skipped due to missing grounding content.")
                section_status.append(
                    {
                        "section_type": section_type,
                        "status": "skipped",
                        "debug": result.get("debug", {}),
                    }
                )
                continue
            sections_output.append(
                {
                    "section_type": section_type,
                    "text": result.get("draft_text", ""),
                    "length_target": result.get("length_target", {}),
                    "citations": result.get("citations", []),
                    "debug": result.get("debug", {}),
                }
            )
            section_status.append(
                {
                    "section_type": section_type,
                    "status": "generated",
                    "debug": result.get("debug", {}),
                }
            )
            warnings.extend(section_warnings or [])
            rolling_approved.append(
                {
                    "section_id": result.get("section_id"),
                    "section_type": section_type,
                    "text": result.get("draft_text", ""),
                    "template_id": template_id,
                }
            )

        combined_parts = []
        for section in sections_output:
            header = self._display_header(section["section_type"])
            combined_parts.append(f"{header}\n{section['text']}".strip())
        combined_text = "\n\n".join(combined_parts)

        return {
            "company_id": company_id,
            "doc_type": doc_type,
            "sections": sections_output,
            "section_status": section_status,
            "section_order": section_order,
            "combined_text": combined_text,
            "warnings": warnings,
            "meta": {
                "section_source": source,
                "generated_at": datetime.utcnow().isoformat(),
                "section_order": section_order,
                "template_id": template_id,
            },
            "approved_sections": rolling_approved,
            "section_queue": section_queue_override,
        }

    def get_section_order(self, company_id: str, doc_type: Optional[str]) -> tuple[List[str], str, Optional[str]]:
        # 1) Try Supabase template tables when flag is on
        if SECTION_BY_SECTION_GENERATION and (not SECTION_BY_SECTION_ALLOWLIST or (doc_type or "").lower() in SECTION_BY_SECTION_ALLOWLIST):
            tmpl_order, tmpl_id = self._load_template_sections_supabase(company_id, doc_type)
            if tmpl_order:
                return tmpl_order, "template_supabase", tmpl_id

        # 2) Infer from stored chunks
        inferred = self._infer_sections_from_chunks(company_id, doc_type)
        if inferred:
            if len(inferred) >= MIN_INFERRED_SECTIONS:
                return inferred, "inferred", None
            return SAFETY_FALLBACK_SECTIONS, "safety_default", None

        # 3) Fallback default
        return DEFAULT_SECTION_ORDER, "default", None

    def _ensure_core_sections(self, section_order: List[str]) -> List[str]:
        ordered = list(dict.fromkeys(section_order))
        for section in CORE_REPORT_SECTIONS:
            if section not in ordered:
                if section == "executive_summary":
                    ordered.insert(0, section)
                else:
                    ordered.append(section)
        return ordered

    def _display_header(self, section_type: str) -> str:
        return DISPLAY_LABELS.get(section_type, section_type.replace("_", " ").title())

    def _load_template_sections_supabase(self, company_id: str, doc_type: Optional[str]) -> tuple[List[str], Optional[str]]:
        """
        Load template sections from Supabase tables (document_templates + template_sections).
        """
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key or not doc_type:
            return [], None
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        try:
            tmpl_resp = requests.get(
                f"{url}/rest/v1/document_templates",
                params={
                    "company_id": f"eq.{company_id}",
                    "doc_type": f"eq.{doc_type}",
                    "is_active": "eq.true",
                    "order": "version.desc",
                    "limit": "1",
                    "select": "template_id",
                },
                headers=headers,
                timeout=10,
            )
            tmpl_resp.raise_for_status()
            tmpl_data = tmpl_resp.json()
            if not tmpl_data:
                return [], None
            template_id = tmpl_data[0].get("template_id")
            if not template_id:
                return [], None

            sec_resp = requests.get(
                f"{url}/rest/v1/template_sections",
                params={
                    "template_id": f"eq.{template_id}",
                    "order": "position_order",
                    "select": "section_type,position_order",
                },
                headers=headers,
                timeout=10,
            )
            sec_resp.raise_for_status()
            sec_data = sec_resp.json()
            section_order = [row["section_type"] for row in sec_data if row.get("section_type")]
            return section_order, template_id
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Supabase template fetch failed for company=%s doc_type=%s: %s", company_id, doc_type, exc)
            return [], None

    def _infer_sections_from_chunks(self, company_id: str, doc_type: Optional[str]) -> List[str]:
        try:
            conn = self.metadata_db._connect()  # type: ignore[attr-defined]
        except Exception:
            return []
        conditions = ["company_id = ?", "section_type IS NOT NULL", "section_type != ''"]
        params: List[Any] = [company_id]
        if doc_type:
            conditions.append("doc_type = ?")
            params.append(doc_type)
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT DISTINCT section_type
            FROM chunks
            WHERE {where_clause}
        """
        try:
            rows = conn.execute(query, params).fetchall()
            section_types = [row["section_type"] for row in rows if row["section_type"] not in (None, "", "unknown")]
            section_types = list(dict.fromkeys(section_types))  # preserve order, drop dupes
            if not section_types:
                return []
            sorted_sections = preferred_sort(section_types)
            # Append any unknown sections (not in preferred list) at the end, preserving discovery order
            known_set = set(DEFAULT_SECTION_ORDER)
            extras = [s for s in section_types if s not in known_set]
            for extra in extras:
                if extra not in sorted_sections:
                    sorted_sections.append(extra)
            return sorted_sections
        except Exception:
            return []
        finally:
            conn.close()

    def _infer_doc_type(self, user_request: str) -> Optional[str]:
        text = user_request.lower()
        if "design report" in text or "rp" in text:
            return "design_report"
        if "calculation" in text:
            return "calculation_narrative"
        if "proposal" in text or "rfp" in text:
            return "proposal"
        return None
