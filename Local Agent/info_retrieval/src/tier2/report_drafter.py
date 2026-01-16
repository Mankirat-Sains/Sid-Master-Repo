from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from tier2.generator import Tier2Generator
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
        section_order, source = self.get_section_order(company_id, doc_type)
        section_order = self._ensure_core_sections(section_order)

        sections_output: List[Dict[str, Any]] = []
        section_status: List[Dict[str, Any]] = []
        warnings: List[str] = []

        for section_type in section_order:
            result = self.generator.draft_section(
                company_id=company_id,
                user_request=user_request,
                overrides={
                    "doc_type": doc_type,
                    "section_type": section_type,
                    "template_id": template_id,
                    "doc_type_variant": doc_type_variant,
                    **(overrides or {}),
                },
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
            "meta": {"section_source": source, "generated_at": datetime.utcnow().isoformat(), "section_order": section_order},
        }

    def get_section_order(self, company_id: str, doc_type: Optional[str]) -> tuple[List[str], str]:
        # 1) Try template table if it exists
        template_order = self._load_template_sections(company_id, doc_type)
        if template_order:
            return template_order, "template"

        # 2) Infer from stored chunks
        inferred = self._infer_sections_from_chunks(company_id, doc_type)
        if inferred:
            if len(inferred) >= MIN_INFERRED_SECTIONS:
                return inferred, "inferred"
            return SAFETY_FALLBACK_SECTIONS, "safety_default"

        # 3) Fallback default
        return DEFAULT_SECTION_ORDER, "default"

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

    def _load_template_sections(self, company_id: str, doc_type: Optional[str]) -> List[str]:
        """
        If a document_templates table exists in metadata DB with columns (company_id, doc_type, section_order TEXT JSON),
        use it. Otherwise return [].
        """
        try:
            conn = self.metadata_db._connect()  # type: ignore[attr-defined]
        except Exception:
            return []
        try:
            query = """
                SELECT section_order
                FROM document_templates
                WHERE company_id = ? AND (? IS NULL OR doc_type = ?)
                ORDER BY updated_at DESC LIMIT 1
            """
            row = conn.execute(query, (company_id, doc_type, doc_type)).fetchone()
            if not row or not row[0]:
                return []
            import json

            data = json.loads(row[0])
            if isinstance(data, list):
                return [s for s in data if s]
        except Exception:
            return []
        finally:
            conn.close()
        return []

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
