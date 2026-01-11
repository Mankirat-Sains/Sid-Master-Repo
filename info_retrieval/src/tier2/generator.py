from __future__ import annotations

from typing import Any, Dict, List, Optional

from retrieval.retriever import Retriever
from storage.metadata_db import MetadataDB
from tier2.llm_client import LLMClient
from tier2.query_analyzer import QueryAnalyzer
from tier2.rag_prompt import build_prompt
from tier2.section_profile import SectionProfileLoader


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

        length_target = self.section_profiles.load(company_id, doc_type, section_type)

        content_filters = {"company_id": company_id, "index_type": "content"}
        style_filters = {"company_id": company_id, "index_type": "style"}
        if doc_type:
            content_filters["doc_type"] = doc_type
            style_filters["doc_type"] = doc_type
        if section_type:
            content_filters["section_type"] = section_type
            style_filters["section_type"] = section_type

        content_chunks = self.retriever.retrieve_for_query(
            query_text=user_request,
            company_id=company_id,
            chunk_type="content",
            top_k=6,
            filters=content_filters,
        )
        style_chunks = self.retriever.retrieve_for_query(
            query_text=user_request,
            company_id=company_id,
            chunk_type="style",
            top_k=4,
            filters=style_filters,
        )

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
