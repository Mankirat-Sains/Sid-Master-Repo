from __future__ import annotations

from typing import Dict, Optional

from storage.metadata_db import MetadataDB

DEFAULTS = {
    "executive_summary": (700, 1100),
    "background": (1200, 1800),
    "introduction": (1200, 1800),
    "scope": (1000, 1600),
    "methodology": (1200, 1800),
    "analysis": (1500, 2200),
    "findings": (1500, 2200),
    "results": (1200, 1800),
    "detailed_analysis": (1600, 2400),
    "recommendations": (900, 1300),
    "conclusion": (600, 900),
    "limitations": (600, 900),
    "general": (900, 1300),
}


class SectionProfileLoader:
    def __init__(self, metadata_db: MetadataDB) -> None:
        self.metadata_db = metadata_db

    def load(
        self, company_id: str, doc_type: Optional[str], section_type: Optional[str]
    ) -> Dict[str, int | None]:
        min_default, max_default = DEFAULTS.get(section_type or "general", DEFAULTS["general"])
        try:
            profile = self.metadata_db.get_section_profile(company_id, doc_type, section_type) if section_type else None
        except Exception:
            profile = None
        if not profile or not profile.get("avg_chars"):
            return {
                "min_chars": min_default,
                "max_chars": max_default,
                "avg_sentences": None,
                "avg_sentence_length": None,
                "avg_paragraphs": None,
            }
        avg_chars = profile["avg_chars"]
        min_chars = max(80, int(round(avg_chars * 0.7)))
        max_chars = int(round(avg_chars * 1.3))
        if profile.get("min_chars"):
            min_chars = max(min_chars, int(profile["min_chars"]))
        if profile.get("max_chars"):
            max_chars = min(max_chars, int(profile["max_chars"]))
        return {
            "min_chars": min_chars,
            "max_chars": max_chars,
            "avg_sentences": profile.get("avg_sentences"),
            "avg_sentence_length": profile.get("avg_sentence_length"),
            "avg_paragraphs": profile.get("avg_paragraphs"),
        }
