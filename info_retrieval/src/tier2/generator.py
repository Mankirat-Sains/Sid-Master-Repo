from __future__ import annotations

from typing import Any, Dict, List, Optional

from retrieval.retriever import Retriever
from storage.metadata_db import MetadataDB
from tier2.llm_client import LLMClient
from tier2.query_analyzer import QueryAnalyzer
from tier2.rag_prompt import build_prompt
from tier2.section_profile import SectionProfileLoader

TEMPLATE_SAFE_SECTIONS = {"introduction", "scope", "methodology"}


class Tier2Generator:
    """
    Orchestrates Tier 2 RAG-based document generation.
    """

    def __init__(
        self,
        retriever: Retriever,
        metadata_db: MetadataDB,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.retriever = retriever
        self.metadata_db = metadata_db
        self.llm_client = llm_client or LLMClient()
        self.analyzer = QueryAnalyzer()
        self.section_profiles = SectionProfileLoader(metadata_db)

    def draft_section(self, company_id: str, user_request: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        analysis = self.analyzer.analyze(user_request)
        doc_type = analysis.get("doc_type")
        section_type = analysis.get("section_type")
        engineering_function = analysis.get("engineering_function")

        overrides = overrides or {}
        doc_type = overrides.get("doc_type", doc_type)
        section_type = overrides.get("section_type", section_type)
        length_target = self.section_profiles.load(company_id, doc_type, section_type)

        content_chunks, content_warnings, content_source = self._retrieve_with_fallbacks(
            query_text=user_request,
            company_id=company_id,
            chunk_type="content",
            top_k=6,
            doc_type=doc_type,
            section_type=section_type,
        )
        style_chunks, style_warnings, style_source = self._retrieve_with_fallbacks(
            query_text=user_request,
            company_id=company_id,
            chunk_type="style",
            top_k=4,
            doc_type=doc_type,
            section_type=section_type,
        )

        warnings: List[str] = []
        warnings.extend(content_warnings)
        warnings.extend(style_warnings)

        if not content_chunks:
            if self._template_allowed(section_type):
                warnings.append(
                    f"No grounding content for section '{section_type or 'section'}'; generated using template-safe mode (no new facts, use [TBD] for specifics)."
                )
                draft_text = self._generate_template_section(section_type or "section", doc_type, user_request, style_chunks, length_target)
                return {
                    "draft_text": draft_text,
                    "doc_type": doc_type,
                    "section_type": section_type,
                    "length_target": {"min_chars": length_target.get("min_chars"), "max_chars": length_target.get("max_chars")},
                    "citations": [],
                    "warnings": warnings,
                    "debug": {
                        "content_chunks_used": 0,
                        "content_source": content_source,
                        "style_chunks_used": len(style_chunks),
                        "style_source": style_source,
                        "mode": "template",
                    },
                }
            warnings.append(f"No grounding content for section '{section_type or 'section'}'; skipped.")
            return {
                "draft_text": "[TBD – insufficient source content]",
                "doc_type": doc_type,
                "section_type": section_type,
                "length_target": {"min_chars": length_target.get("min_chars"), "max_chars": length_target.get("max_chars")},
                "citations": [],
                "warnings": warnings,
                "debug": {
                    "content_chunks_used": 0,
                    "content_source": content_source,
                    "style_chunks_used": len(style_chunks),
                    "style_source": style_source,
                    "mode": "skipped_no_content",
                },
            }

        task = {
            "doc_type": doc_type,
            "section_type": section_type or "section",
            "engineering_function": engineering_function,
        }
        prompt = build_prompt(task, length_target, style_chunks, content_chunks)
        draft_text = self.llm_client.generate_chat(
            system_prompt="You are an engineering documentation writer. Match the company's tone. Do not invent facts. Only use provided facts. If a value is missing, use [TBD].",
            user_prompt=prompt,
            max_tokens=800,
        )
        draft_text = self._enforce_length(draft_text, length_target)

        return {
            "draft_text": draft_text,
            "doc_type": doc_type,
            "section_type": section_type,
            "length_target": {"min_chars": length_target.get("min_chars"), "max_chars": length_target.get("max_chars")},
            "citations": self._format_citations(content_chunks),
            "warnings": warnings,
            "debug": {
                "content_chunks_used": len(content_chunks),
                "content_source": content_source,
                "style_chunks_used": len(style_chunks),
                "style_source": style_source,
                "mode": "grounded",
            },
        }

    def _enforce_length(self, text: str, length_target: Dict[str, Any]) -> str:
        min_chars = length_target.get("min_chars")
        max_chars = length_target.get("max_chars")
        if not min_chars or not max_chars:
            return text.strip()
        if min_chars <= len(text) <= max_chars:
            return text.strip()
        rewrite_prompt = (
            f"Rewrite the following section to be between {min_chars} and {max_chars} characters. "
            "Preserve tone, style, and facts. No new facts. Plain text only.\n\n"
            f"---\n{text}\n---"
        )
        rewritten = self.llm_client.generate_chat(
            system_prompt="You are an engineering documentation writer. Keep within specified length and do not add facts.",
            user_prompt=rewrite_prompt,
            max_tokens=800,
        )
        return rewritten.strip()

    def _retrieve_with_fallbacks(
        self,
        query_text: str,
        company_id: str,
        chunk_type: str,
        top_k: int,
        doc_type: Optional[str],
        section_type: Optional[str],
    ) -> tuple[List[Dict[str, Any]], List[str], str]:
        warnings: List[str] = []
        filters_base = {"company_id": company_id, "index_type": chunk_type}
        attempts = [
            {**filters_base, **({"doc_type": doc_type} if doc_type else {}), **({"section_type": section_type} if section_type else {})},
            {**filters_base, **({"doc_type": doc_type} if doc_type else {})},
            filters_base,
        ]
        results: List[Dict[str, Any]] = []
        source_label = "company"
        for idx, filt in enumerate(attempts):
            results = self.retriever.retrieve_for_query(
                query_text=query_text,
                company_id=company_id,
                chunk_type=chunk_type,
                top_k=top_k,
                filters=filt,
            )
            if results:
                if idx > 0:
                    warnings.append(f"{chunk_type} retrieval fell back to broader filters (attempt {idx+1}).")
                source_label = self._describe_filter(filt)
                break
        return results, warnings, source_label

    def _template_allowed(self, section_type: Optional[str]) -> bool:
        if not section_type:
            return False
        return section_type in TEMPLATE_SAFE_SECTIONS

    def _generate_template_section(
        self,
        section_type: str,
        doc_type: Optional[str],
        user_request: str,
        style_chunks: List[Dict[str, Any]],
        length_target: Dict[str, Any],
    ) -> str:
        style_bullets = []
        for chunk in style_chunks[:4]:
            text = chunk.get("text", "")
            if text:
                style_bullets.append(text.strip())
        style_hint = "\n".join(f"- {t}" for t in style_bullets if t)

        user_prompt = (
            f"Write a high-level {section_type.replace('_', ' ')} section for a {doc_type or 'report'}. "
            "Use neutral, company-consistent tone. Do not invent facts or numbers; use [TBD] for any specifics. "
            "Keep it brief and template-like so it can be filled later.\n"
            f"User request: {user_request}\n"
        )
        if style_hint:
            user_prompt += f"\nStyle cues (examples of voice to mimic):\n{style_hint}\n"
        draft = self.llm_client.generate_chat(
            system_prompt="You are writing a placeholder section that must avoid factual claims. Keep it generic, no numbers, use [TBD] for specifics, and match the provided voice cues.",
            user_prompt=user_prompt,
            max_tokens=600,
            temperature=0.4,
        )
        return self._enforce_length(draft, length_target)

    def _describe_filter(self, filt: Dict[str, Any]) -> str:
        keys: List[str] = []
        if filt.get("section_type"):
            keys.append("section")
        if filt.get("doc_type"):
            keys.append("doc_type")
        if filt.get("artifact_id"):
            keys.append("artifact")
        if not keys:
            return "company"
        return "+".join(keys)

    def _format_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            citations.append(
                {
                    "artifact_id": meta.get("artifact_id"),
                    "version_id": meta.get("version_id"),
                    "heading": meta.get("heading"),
                    "page_number": meta.get("page_number"),
                    "chunk_id": meta.get("chunk_id"),
                    "score": chunk.get("score"),
                }
            )
        return citations
