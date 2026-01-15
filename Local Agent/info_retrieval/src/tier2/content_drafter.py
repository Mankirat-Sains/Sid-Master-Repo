"""
Tier 2 content-only drafter.
Recreates section text using company length/style signals without formatting.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from retrieval.retriever import Retriever
from storage.metadata_db import MetadataDB


DEFAULT_LENGTH_FALLBACK = {"min_chars": 400, "max_chars": 900, "avg_sentences": 5}


@dataclass
class DraftResult:
    draft_text: str
    section_type: str
    length_target: Dict[str, float | int | None]
    citations: List[Dict[str, Any]]


def analyze_request(user_request: str) -> Dict[str, Optional[str]]:
    """
    Deterministic request analyzer per requirements.
    """
    text = user_request.lower()
    section_type = None
    if "introduction" in text:
        section_type = "introduction"
    elif "methodology" in text:
        section_type = "methodology"
    elif "conclusion" in text:
        section_type = "conclusion"
    elif "recommendation" in text:
        section_type = "recommendations"

    doc_type = None
    if "design report" in text:
        doc_type = "design_report"
    elif "calculation" in text:
        doc_type = "calculation_narrative"

    return {
        "doc_type": doc_type or "design_report",
        "section_type": section_type or "introduction",
        "engineering_function": "describe_section",
        "constraints": {},
    }


class ContentDrafter:
    """
    Drafts section text that matches company voice and typical length.
    """

    def __init__(
        self,
        retriever: Retriever,
        metadata_db: MetadataDB,
        llm_client: Any,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.retriever = retriever
        self.metadata_db = metadata_db
        self.llm_client = llm_client
        self.model = model

    def draft_section(self, company_id: str, user_request: str) -> DraftResult:
        params = analyze_request(user_request)
        section_type = params["section_type"]
        doc_type = params["doc_type"]

        profile = self.metadata_db.get_section_profile(company_id, doc_type, section_type)
        length_target = self._build_length_target(profile)

        content_chunks = self.retriever.retrieve_content(
            query_text=user_request,
            company_id=company_id,
            top_k=5,
            filters={"doc_type": doc_type, "section_type": section_type},
        )
        style_chunks = self.retriever.retrieve_for_query(
            query_text=user_request,
            company_id=company_id,
            chunk_type="style",
            top_k=3,
            filters={"section_type": section_type, "doc_type": doc_type},
        )

        prompt = self._build_prompt(section_type, length_target, content_chunks, style_chunks)
        draft_text = self._call_llm(prompt)
        draft_text = self._enforce_length(draft_text, length_target)
        citations = self._format_citations(content_chunks)

        return DraftResult(
            draft_text=draft_text,
            section_type=section_type,
            length_target=length_target,
            citations=citations,
        )

    def _build_length_target(self, profile: Optional[Dict[str, Any]]) -> Dict[str, float | int | None]:
        if not profile or not profile.get("avg_chars"):
            base = DEFAULT_LENGTH_FALLBACK["min_chars"]
            return {
                "min_chars": base,
                "max_chars": DEFAULT_LENGTH_FALLBACK["max_chars"],
                "avg_sentences": DEFAULT_LENGTH_FALLBACK["avg_sentences"],
                "avg_sentence_length": None,
                "avg_paragraphs": None,
            }

        avg_chars = profile["avg_chars"]
        min_chars = max(80, int(round(avg_chars * 0.7)))
        max_chars = int(round(avg_chars * 1.3))
        # Respect observed min/max if present but keep clamped to avoid outliers.
        if profile.get("min_chars"):
            min_chars = max(min_chars, int(profile["min_chars"]))
        if profile.get("max_chars"):
            max_chars = min(max_chars, int(profile["max_chars"]))

        return {
            "min_chars": min_chars,
            "max_chars": max_chars,
            "avg_sentences": profile.get("avg_sentences") or DEFAULT_LENGTH_FALLBACK["avg_sentences"],
            "avg_sentence_length": profile.get("avg_sentence_length"),
            "avg_paragraphs": profile.get("avg_paragraphs"),
        }

    def _build_prompt(
        self,
        section_type: str,
        length_target: Dict[str, float | int | None],
        content_chunks: List[Dict[str, Any]],
        style_chunks: List[Dict[str, Any]],
    ) -> str:
        min_chars = length_target["min_chars"]
        max_chars = length_target["max_chars"]
        avg_sentences = length_target.get("avg_sentences") or ""
        bullet_pattern = re.compile(r"(^|\n)\s*[-•\*]\s+")
        examples_have_bullets = False

        parts: List[str] = []
        parts.append("You are an engineering report writer. Match the company’s writing style exactly.")
        parts.append("Do not invent facts. Do not exceed length limits.\n")

        parts.append(f"Section: {section_type}")
        parts.append(f"Target length: {min_chars}–{max_chars} characters")
        parts.append(f"Typical sentences: {avg_sentences}\n")

        if style_chunks:
            parts.append("Style guidance (examples):")
            for chunk in style_chunks[:3]:
                snippet = (chunk.get("text", "") or "")[:500]
                if bullet_pattern.search(snippet):
                    examples_have_bullets = True
                parts.append(f"- \"{snippet}\"")
            parts.append("Use similar wording and sentence structure, but do NOT copy verbatim.\n")

        if content_chunks:
            parts.append("Content to use (facts):")
            for idx, chunk in enumerate(content_chunks[:5], 1):
                meta = chunk.get("metadata", {})
                heading = meta.get("heading") or meta.get("section_type") or "Unknown"
                text = (chunk.get("text", "") or "")[:400]
                parts.append(f"[{idx}] {heading}: {text}")
            parts.append("Base your writing ONLY on these facts.\n")

        parts.append("Hard constraints:")
        parts.append(f"- Output must be between {min_chars} and {max_chars} characters.")
        parts.append("- Formal professional tone; third-person voice.")
        if examples_have_bullets:
            parts.append("- Bullets allowed if needed.")
        else:
            parts.append("- No bullet points.")
        parts.append("- Plain text only.")

        parts.append("\nWrite the section now.")
        return "\n".join(parts)

    def _call_llm(self, prompt: str) -> str:
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an engineering report writer. Match the company’s writing style exactly. Do not invent facts. Do not exceed length limits."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _format_citations(self, content_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        for chunk in content_chunks:
            meta = chunk.get("metadata", {})
            citations.append(
                {
                    "artifact_id": meta.get("artifact_id"),
                    "version_id": meta.get("version_id"),
                    "heading": meta.get("heading"),
                    "page_number": meta.get("page_number"),
                    "chunk_id": meta.get("chunk_id"),
                }
            )
        return citations

    def _enforce_length(self, draft_text: str, length_target: Dict[str, float | int | None]) -> str:
        min_chars = int(length_target["min_chars"])
        max_chars = int(length_target["max_chars"])
        if min_chars <= len(draft_text) <= max_chars:
            return draft_text
        rewrite_prompt = (
            f"Rewrite the following section to be between {min_chars} and {max_chars} characters. "
            "Preserve tone, voice, and all facts. Do not add new facts. Plain text only.\n\n"
            f"---\n{draft_text}\n---"
        )
        return self._call_llm(rewrite_prompt)
