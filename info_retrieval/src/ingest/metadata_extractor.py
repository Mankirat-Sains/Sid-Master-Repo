from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..utils.classifier_provider import ClassifierProvider
from ..utils.logger import get_logger
from .document_parser import ParsedDocument, generate_artifact_id, generate_version_id

logger = get_logger(__name__)


@dataclass
class MetadataExtractor:
    """
    Rules-first metadata extractor with a pluggable classifier.
    """

    classifier: ClassifierProvider = field(default_factory=lambda: RulesBasedClassifier())

    def extract_metadata(self, document: ParsedDocument, company_id: Optional[str] = None) -> Dict[str, Any]:
        artifact_id = document.artifact_id or generate_artifact_id(document.metadata.get("file_path", "unknown"), company_id)
        version_id = document.version_id or generate_version_id(document.text)

        section_types = self.classifier.classify_sections(document)
        doc_type = self.classifier.classify_doc_type(document)
        calc_type = self.classifier.classify_calc_type(document)

        return {
            "artifact_id": artifact_id,
            "version_id": version_id,
            "company_id": company_id or document.metadata.get("company_id"),
            "source": document.metadata.get("source", "upload"),
            "doc_type": doc_type,
            "section_types": section_types,
            "project_name": self._extract_project_name(document),
            "author": self._extract_author(document),
            "reviewer": document.metadata.get("reviewer"),
            "date": self._extract_date(document),
            "calculation_type": calc_type,
            "table_count": len(document.tables),
            "section_count": len(document.sections),
        }

    def _extract_project_name(self, document: ParsedDocument) -> Optional[str]:
        patterns = [r"Project[:\-]\s*(.+)", r"Project Name[:\-]\s*(.+)"]
        for pattern in patterns:
            match = re.search(pattern, document.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return document.metadata.get("project_name")

    def _extract_author(self, document: ParsedDocument) -> Optional[str]:
        patterns = [r"Author[:\-]\s*(.+)", r"Prepared by[:\-]\s*(.+)"]
        for pattern in patterns:
            match = re.search(pattern, document.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return document.metadata.get("author")

    def _extract_date(self, document: ParsedDocument) -> Optional[str]:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", document.text)
        if match:
            return match.group(1)
        match = re.search(r"(\d{2}/\d{2}/\d{4})", document.text)
        if match:
            return match.group(1)
        return document.metadata.get("date")


class RulesBasedClassifier(ClassifierProvider):
    """
    Deterministic classifier using headings, styles, and keywords.
    """

    def classify_doc_type(self, document: ParsedDocument) -> str:
        text_lower = document.text.lower()
        candidates = [
            ("calculation", ["calculation", "calc.", "calculations"]),
            ("design_report", ["design report", "design basis", "engineering report"]),
            ("narrative", ["narrative", "description", "overview"]),
            ("specification", ["specification", "spec."]),
        ]
        for doc_type, keywords in candidates:
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        if any("table" in (section.title.lower()) for section in document.sections):
            return "calculation"
        return "general"

    def classify_sections(self, document: ParsedDocument) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for section in document.sections:
            section_type = self._detect_section_type(section.title)
            mapping[section.title] = section_type
        return mapping

    def classify_calc_type(self, document: ParsedDocument) -> Optional[str]:
        text_lower = document.text.lower()
        if any(keyword in text_lower for keyword in ["beam", "column", "shear", "moment", "structural"]):
            return "structural"
        if any(keyword in text_lower for keyword in ["thermal", "heat", "temperature"]):
            return "thermal"
        if any(keyword in text_lower for keyword in ["electrical", "voltage", "current", "load"]):
            return "electrical"
        return None

    def _detect_section_type(self, title: str) -> str:
        lower = title.lower()
        if "introduction" in lower or lower.startswith("1."):
            return "introduction"
        if "method" in lower or "approach" in lower:
            return "methodology"
        if "result" in lower:
            return "results"
        if "conclusion" in lower or "summary" in lower:
            return "conclusions"
        if "scope" in lower:
            return "scope"
        return "general"


class LLMClassifier(ClassifierProvider):
    """
    Optional classifier stub for future LLM-powered disambiguation.
    """

    def __init__(self, client: Any = None) -> None:
        self.client = client

    def classify_doc_type(self, document: ParsedDocument) -> str:
        logger.warning("LLMClassifier is not fully implemented; returning 'general'.")
        return "general"

    def classify_sections(self, document: ParsedDocument) -> Dict[str, str]:
        logger.warning("LLMClassifier is not fully implemented; returning empty mapping.")
        return {}

    def classify_calc_type(self, document: ParsedDocument) -> Optional[str]:
        return None
