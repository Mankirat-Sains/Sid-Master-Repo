"""
Document Drafter: Tier 2 generation engine.
Combines templates + retrieval + LLM to draft sections.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from tier2.query_analyzer import QueryAnalyzer, StructuredQuery
from tier2.template_store import TemplateStore
from retrieval.retriever import Retriever


class DocumentDrafter:
    """
    Generate document sections using templates + retrieval + LLM.
    """

    def __init__(
        self,
        template_store: TemplateStore,
        retriever: Retriever,
        llm_client: Any,
        model: str = "gpt-4o-mini",
    ):
        self.query_analyzer = QueryAnalyzer()
        self.template_store = template_store
        self.retriever = retriever
        self.llm_client = llm_client
        self.model = model

    def draft_section(
        self, company_id: str, user_request: str, constraints_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Draft a document section based on user request.
        """
        # Step 1: Analyze query
        query = self.query_analyzer.analyze(user_request)
        if constraints_override:
            query["constraints"].update(constraints_override)

        # Step 2: Fetch templates and rules
        section_template = self.template_store.get_section_template(
            company_id, query["doc_type"], query["section_type"]
        )
        style_rules = self.template_store.get_style_rules(company_id)

        # Step 3: Retrieve content chunks
        primary_filters = {**{"doc_type": query["doc_type"], "section_type": query["section_type"]}, **query["constraints"]}
        content_chunks = self.retriever.retrieve_content(
            query_text=user_request,
            company_id=company_id,
            filters=primary_filters,
            top_k=8,
        )
        if not content_chunks:
            # Relax filters to allow any section/doc_type for this company
            fallback_filters = {"company_id": company_id}
            content_chunks = self.retriever.retrieve_content(
                query_text=user_request,
                company_id=company_id,
                filters=fallback_filters,
                top_k=8,
            )

        # Step 4: Retrieve style exemplars
        style_chunks = self.retriever.retrieve_style_examples(
            section_type=query["section_type"], company_id=company_id, top_k=3
        )
        if not style_chunks:
            style_chunks = self.retriever.retrieve_style_examples(
                section_type=None, company_id=company_id, top_k=3
            )

        # Step 5: Build LLM prompt
        prompt = self._build_prompt(
            query=query,
            section_template=section_template,
            style_rules=style_rules,
            content_chunks=content_chunks,
            style_chunks=style_chunks,
            user_request=user_request,
        )

        # Step 6: Call LLM
        draft_text = self._call_llm(prompt)

        # Step 7: Prepare citations
        citations = self._format_citations(content_chunks + style_chunks)

        return {
            "draft_text": draft_text,
            "used_template": {
                "doc_type": query["doc_type"],
                "section_type": query["section_type"],
                "template_id": section_template["id"] if section_template else None,
            },
            "citations": citations,
        }

    def _build_prompt(
        self,
        query: StructuredQuery,
        section_template: Optional[Dict[str, Any]],
        style_rules: List[Dict[str, Any]],
        content_chunks: List[Dict[str, Any]],
        style_chunks: List[Dict[str, Any]],
        user_request: str,
    ) -> str:
        """Build complete LLM prompt from all inputs."""
        parts: List[str] = []

        # System context
        parts.append(
            "You are an engineering documentation writer. Your task is to draft a technical document section "
            "following company templates and style guidelines strictly."
        )
        parts.append("")

        # Style rules
        if style_rules:
            parts.append("## COMPANY STYLE RULES (MANDATORY)")
            parts.append("Follow these rules exactly:")
            for rule in style_rules:
                parts.append(f"\n**{rule.get('rule_type', '').upper()}**:")
                parts.append(rule.get("rules", ""))
                banned = rule.get("banned_phrases")
                preferred = rule.get("preferred_phrases")
                if banned:
                    parts.append(f"NEVER use: {', '.join(banned)}")
                if preferred:
                    parts.append(f"PREFER: {', '.join(preferred)}")
            parts.append("")

        # Section template
        if section_template:
            parts.append("## SECTION TEMPLATE")
            parts.append("Follow this structure:")
            parts.append(section_template.get("skeleton", ""))
            if section_template.get("required_elements"):
                parts.append(f"\nRequired elements: {section_template['required_elements']}")
            parts.append("")

        # Style exemplars
        if style_chunks:
            parts.append("## WRITING STYLE EXAMPLES")
            parts.append("Match the writing style of these examples from similar sections:")
            for i, chunk in enumerate(style_chunks[:3], 1):
                heading = chunk.get("metadata", {}).get("heading", "Unknown")
                text = chunk.get("text", "")[:300]
                parts.append(f"\nExample {i} (from {heading}):")
                parts.append(f'"{text}..."')
            parts.append("")

        # Content chunks (facts)
        if content_chunks:
            parts.append("## RELEVANT CONTENT (SOURCE MATERIAL)")
            parts.append("Use these facts and data in your draft. Cite them appropriately:")
            for i, chunk in enumerate(content_chunks[:8], 1):
                metadata = chunk.get("metadata", {})
                artifact = metadata.get("artifact_id", "unknown")
                heading = metadata.get("heading", "Unknown")
                text = chunk.get("text", "")[:400]
                parts.append(f"\n[Source {i}] Artifact: {artifact}, Section: {heading}")
                parts.append(f"{text}")
            parts.append("")

        # Constraints
        if query["constraints"]:
            parts.append("## SPECIFIC REQUIREMENTS")
            for key, value in query["constraints"].items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        # Task
        parts.append("## YOUR TASK")
        parts.append(f"Draft a {query['section_type']} section for a {query['doc_type']}.")
        parts.append(f"User request: \"{user_request}\"")
        parts.append("")
        parts.append("IMPORTANT:")
        parts.append("- Do NOT invent numbers, calculations, or data. Use placeholders like [TBD] if information is missing.")
        parts.append("- Follow the company style rules exactly.")
        parts.append("- Match the tone and structure of the style examples.")
        parts.append("- Reference source material where appropriate.")
        parts.append("- Output ONLY the drafted section text. No preamble, no meta-commentary.")

        return "\n".join(parts)

    def _call_llm(self, prompt: str) -> str:
        """Call LLM (OpenAI-compatible client) to generate draft."""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                max_tokens=800,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as exc:
            raise RuntimeError(f"LLM call failed: {exc}")

    def _format_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format chunk metadata as citations."""
        citations: List[Dict[str, Any]] = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            citations.append(
                {
                    "artifact_id": metadata.get("artifact_id"),
                    "version_id": metadata.get("version_id"),
                    "heading": metadata.get("heading"),
                    "page_number": metadata.get("page_number"),
                    "chunk_id": chunk.get("id"),
                    "score": chunk.get("score", 0),
                    "index_type": metadata.get("index_type", "content"),
                }
            )
        return citations
