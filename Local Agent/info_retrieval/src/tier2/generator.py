from __future__ import annotations

import re
import traceback
from typing import Any, Dict, List, Optional

from llm_config import get_llm
from retrieval.retriever import Retriever
from storage.metadata_db import MetadataDB
from tier2.llm_client import LLMClient
from tier2.query_analyzer import QueryAnalyzer
from tier2.section_profile import SectionProfileLoader


def _log_text_checkpoint(location_name: str, text: Optional[str]) -> None:
    """Log checkpoints for text generation to trace TBD propagation."""
    snippet = (text or "")[:100]
    stack = traceback.format_stack()
    stack_line = stack[-3].strip() if len(stack) >= 3 else ""
    print(f"📍 CHECKPOINT: {location_name}")
    print(f"   Text: {snippet if snippet else 'None'}")
    print(f"   Contains TBD: {'[TBD' in (text or '')}")
    print(f"   Stack: {stack_line}")


def _format_chunks_for_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks for clear LLM context with source breadcrumbs."""
    formatted: List[str] = []
    for idx, chunk in enumerate(chunks):
        meta = chunk.get("metadata", {}) or {}
        source = meta.get("source") or meta.get("file_path") or meta.get("artifact_id") or "Unknown"
        page = meta.get("page_number") or "N/A"
        text = chunk.get("text") or meta.get("text") or ""
        formatted.append(f"[Source {idx + 1}: {source}, Page {page}]\n{text}\n")
    return "\n".join(formatted)


def _extract_citations_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build citation objects from retrieved chunks."""
    citations: List[Dict[str, Any]] = []
    for chunk in chunks:
        meta = chunk.get("metadata", {}) or {}
        citations.append(
            {
                "artifact_id": meta.get("artifact_id"),
                "source": meta.get("source") or meta.get("file_path"),
                "page_number": meta.get("page_number"),
                "chunk_id": meta.get("chunk_id") or chunk.get("id"),
                "score": chunk.get("score") or meta.get("similarity_score", 0),
            }
        )
    return citations


def _base_doc_id(artifact_id: Optional[str]) -> Optional[str]:
    """Strip trailing hash/variant suffix to group versions of the same doc."""
    if not artifact_id:
        return None
    parts = str(artifact_id).rsplit("_", 1)
    if len(parts) == 2 and len(parts[1]) <= 12:
        doc = parts[0]
    else:
        doc = str(artifact_id)
    doc = re.sub(r"\s*[-_ ]*draft(?:\s*\(\d+\))?(?:-\d+)?$", "", doc, flags=re.IGNORECASE)
    return doc.strip()


def _dedupe_citations_by_doc(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Collapse citations to one per document base (regardless of chunk/page),
    keeping the highest-score entry for that document.
    """
    best: Dict[str, Dict[str, Any]] = {}
    for cite in citations:
        base = _base_doc_id(cite.get("artifact_id")) or cite.get("artifact_id") or "unknown"
        score = cite.get("score") or 0
        if base not in best or score > (best[base].get("score") or 0):
            best[base] = cite
    return list(best.values())


def _convert_extra_context(extra_context: Any) -> List[Dict[str, Any]]:
    """
    Convert pre-fetched graded/retrieved docs into chunk-like dicts so they can
    be merged with retriever results for grounding and citations.
    """
    if extra_context and not isinstance(extra_context, (list, tuple)):
        extra_context = [extra_context]
    chunks: List[Dict[str, Any]] = []
    for doc in extra_context or []:
        text = None
        meta: Dict[str, Any] = {}
        if hasattr(doc, "page_content"):
            text = getattr(doc, "page_content", None)
            meta = getattr(doc, "metadata", {}) or {}
        elif isinstance(doc, dict):
            text = doc.get("page_content") or doc.get("text") or doc.get("content")
            meta = doc.get("metadata", {}) or {}
        if not text:
            continue
        similarity = meta.get("similarity_score") or meta.get("score") or 0.75
        source = meta.get("source") or meta.get("file_path") or meta.get("document_name") or meta.get("artifact_id")
        chunk_meta = {
            "artifact_id": meta.get("artifact_id"),
            "source": source,
            "file_path": meta.get("file_path") or source,
            "page_number": meta.get("page_number") or meta.get("page") or meta.get("page_index"),
            "chunk_id": meta.get("chunk_id"),
            "similarity_score": similarity,
        }
        chunks.append({"text": text, "metadata": chunk_meta, "score": similarity})
    return chunks


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

        overrides = overrides or {}
        extra_context = overrides.get("extra_context") or []
        doc_type = overrides.get("doc_type", doc_type)
        section_type = overrides.get("section_type", section_type)
        length_target = self.section_profiles.load(company_id, doc_type, section_type)
        min_chars = length_target.get("min_chars") or 900
        max_chars = length_target.get("max_chars") or 1300
        target_word_min = max(180, int(round(min_chars / 5.5)))
        target_word_max = int(round(max_chars / 4.5))

        content_chunks, content_warnings, content_source = self._retrieve_with_fallbacks(
            query_text=user_request,
            company_id=company_id,
            chunk_type="content",
            top_k=10,
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

        manual_chunks = _convert_extra_context(extra_context)
        if manual_chunks:
            warnings.append(f"Merged {len(manual_chunks)} pre-fetched context chunks from retrieval/graded docs.")
            content_chunks = manual_chunks + content_chunks
            content_source = f"prefetched+{content_source}"

        print(f"📊 Retrieved {len(content_chunks)} content chunks for generation")
        top_score = max(
            [
                chunk.get("score")
                or (chunk.get("metadata", {}) or {}).get("similarity_score")
                or 0
                for chunk in content_chunks
            ],
            default=0,
        )
        print(f"   Top similarity score: {top_score}")
        score_floor = 0.4
        has_sufficient_data = len(content_chunks) >= 3 and top_score >= 0.6
        has_some_data = len(content_chunks) > 0 and top_score >= score_floor
        has_no_data = not has_some_data

        if has_sufficient_data:
            print("✅ Sufficient data found - generating from retrieved sources")
            prompt = f"""You are drafting the "{section_type or 'section'}" portion of a technical engineering report.

Primary question: "{user_request}"

Retrieved evidence (use as the backbone for assertions):
{_format_chunks_for_context(content_chunks)}

Write a detailed section ({target_word_min}-{target_word_max} words, 3-6 paragraphs) that:
- Opens with one sentence framing the purpose of this section.
- Develops background, analysis, and implications using numbers, dates, locations, and component names from the evidence.
- Calls out risks, constraints, and decisions with the rationale grounded in the sources.
- Closes with a concise takeaway that sets up recommendations or next steps.
- Keep attributions implicit (no bracketed citations or warnings), but base claims only on the provided material.
- Do not include placeholders such as [TBD] or filler text.

Generate the section:"""
            mode = "retrieved"
            data_source = "retrieved"
        elif has_some_data:
            print("⚠️ Limited data found - combining with industry standards")
            print(f"   Limited path detail: top_score={top_score}, using top 5 chunks (of {len(content_chunks)})")
            content_chunks = content_chunks[:5]
            prompt = f"""You are drafting the "{section_type or 'section'}" portion of a technical engineering report.

We found partial evidence relevant to the request:
{_format_chunks_for_context(content_chunks)}

Task: Write a grounded section ({target_word_min}-{target_word_max} words, 3-6 paragraphs) for "{user_request}" that:
1) Leads with what we DO know from the evidence above, weaving in specific figures, dates, and component names.
2) Clearly flags gaps (e.g., "The documentation does not specify X; typical practice is Y") and supplements with industry-standard guidance.
3) Provides actionable context, risks, and next steps tied to the available sources.
Keep attributions implicit (no citation brackets), avoid boilerplate, and do not emit warning banners or placeholders.

Generate the section:"""
            warnings.append("Limited retrieved content; supplementing with industry knowledge.")
            mode = "hybrid"
            data_source = "hybrid"
        else:
            print("❌ No relevant data found - using industry knowledge only")
            prompt = f"""The user asked: "{user_request}"

Our knowledge base does not contain specific information on this topic.

Write a thorough section ({target_word_min}-{target_word_max} words, 3-6 paragraphs) that:
1) Opens by stating that specific internal documentation is unavailable.
2) Provides background, analysis, and key considerations using industry-standard practice for the topic.
3) Outlines risks, constraints, and decision factors, then closes with clear recommendations or next steps.
Keep the tone professional and technical; avoid citations or warning banners and do not use placeholders like [TBD].

Generate the section:"""
            warnings.append("No matching knowledge base content; response is based on general guidance.")
            mode = "general"
            data_source = "general"

        style_hint_lines = [chunk.get("text", "").strip() for chunk in style_chunks[:4] if chunk.get("text")]
        if style_hint_lines:
            prompt += "\nStyle cues from prior documents:\n" + "\n".join(f"- {line}" for line in style_hint_lines)

        system_prompt = (
            "You are an engineering documentation writer producing comprehensive, multi-paragraph report sections. "
            "Prioritize specificity, structure, and completeness using provided evidence."
        )
        try:
            draft_text = self.llm_client.generate_chat(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=2200,
                temperature=0.35 if has_sufficient_data else 0.45,
            )
            _log_text_checkpoint("tier2.grounded_generation", draft_text)
        except Exception as e:  # noqa: BLE001
            print(f"❌ Generation failed: {e}")
            llm = get_llm()
            try:
                response = llm.invoke(prompt)
                draft_text = response.content if hasattr(response, "content") else str(response)
            except Exception:
                draft_text = (
                    f"A comprehensive analysis of {user_request} should combine project specifics with industry standards. "
                    "This placeholder is provided because automated generation failed."
                )
            _log_text_checkpoint("tier2.llm_fallback_no_content", draft_text)

        draft_text = self._enforce_length(draft_text, length_target)
        _log_text_checkpoint("tier2.length_enforced", draft_text)

        # Ensure grounded responses open with the expected prefix
        if has_sufficient_data and draft_text and not draft_text.lower().startswith("based on our documentation"):
            draft_text = f"Based on our documentation, {draft_text.lstrip()}"
        if has_some_data and not has_sufficient_data and draft_text:
            limited_prefix = (
                "WARNING: Limited documentation available. This draft supplements our records with industry-standard guidance."
            )
            # Strip any LLM-inserted warning banners to avoid duplicates
            draft_text = re.sub(
                r"\*?WARNING: Limited documentation available.*?guidance\.?\*?\s*", "", draft_text, flags=re.IGNORECASE | re.DOTALL
            ).strip()
            if not draft_text.lower().startswith("warning: limited documentation available"):
                draft_text = f"{limited_prefix} {draft_text.lstrip()}"

        citations = _extract_citations_from_chunks(content_chunks) if not has_no_data else []
        if citations:
            citations = _dedupe_citations_by_doc(citations)
        print(f"✅ Generated {len(draft_text)} chars")
        print(f"📚 With {len(citations)} citations")

        return {
            "draft_text": draft_text,
            "doc_type": doc_type,
            "section_type": section_type,
            "length_target": {"min_chars": length_target.get("min_chars"), "max_chars": length_target.get("max_chars")},
            "citations": citations,
            "warnings": warnings,
            "data_source": data_source,
            "chunks_used": len(content_chunks),
            "debug": {
                "content_chunks_used": len(content_chunks),
                "content_source": content_source,
                "style_chunks_used": len(style_chunks),
                "style_source": style_source,
                "mode": mode,
            },
        }

    def _enforce_length(self, text: str, length_target: Dict[str, Any]) -> str:
        min_chars = length_target.get("min_chars")
        max_chars = length_target.get("max_chars")
        if not min_chars or not max_chars:
            stripped = text.strip()
            _log_text_checkpoint("tier2.enforce_length_skip", stripped)
            return stripped
        if min_chars <= len(text) <= max_chars:
            stripped = text.strip()
            _log_text_checkpoint("tier2.enforce_length_within_bounds", stripped)
            return stripped
        rewrite_prompt = (
            f"Rewrite the following section to be between {min_chars} and {max_chars} characters. "
            "Preserve tone, style, facts, and any citations like [Source: ...]. No new facts. Keep multi-paragraph structure. Plain text only.\n\n"
            f"---\n{text}\n---"
        )
        rewritten = self.llm_client.generate_chat(
            system_prompt="You are an engineering documentation writer. Keep within specified length and do not add facts.",
            user_prompt=rewrite_prompt,
            max_tokens=2000,
        )
        _log_text_checkpoint("tier2.enforce_length_rewrite", rewritten)
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
        table_name = getattr(getattr(self.retriever, "vector_store", None), "table", "chunks")
        print("🔍 RETRIEVAL CALLED:")
        print(f"   Query: {query_text}")
        print(f"   Table: {table_name}")
        print(f"   Chunk type: {chunk_type}")
        print(f"   Limit: {top_k}")
        print("   Threshold: 0.3")
        for idx, filt in enumerate(attempts):
            results = self.retriever.retrieve_for_query(
                query_text=query_text,
                company_id=company_id,
                chunk_type=chunk_type,
                top_k=top_k,
                filters=filt,
            )
            print(f"📊 RETRIEVAL RESULTS: {len(results)} chunks found (attempt {idx + 1})")
            for i, r in enumerate(results[:3]):
                meta = r.get("metadata", {}) or {}
                src = meta.get("source") or meta.get("file_path") or meta.get("artifact_id") or "Unknown"
                score = r.get("score") or meta.get("similarity_score")
                print(f"   [{i + 1}] {src} (score: {score})")
            if results:
                if idx > 0:
                    warnings.append(f"{chunk_type} retrieval fell back to broader filters (attempt {idx+1}).")
                source_label = self._describe_filter(filt)
                break
        return results, warnings, source_label

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
