from __future__ import annotations

import re
from typing import Any, Dict, List


def detect_bullets(samples: List[str]) -> bool:
    bullet_pattern = re.compile(r"(^|\n)\s*[-•\*]\s+")
    return any(bullet_pattern.search(s or "") for s in samples)


def build_prompt(
    task: Dict[str, str],
    length_target: Dict[str, int | None],
    style_chunks: List[Dict[str, Any]],
    content_chunks: List[Dict[str, Any]],
) -> str:
    section_type = task.get("section_type") or "section"
    doc_type = task.get("doc_type") or "document"
    engineering_function = task.get("engineering_function") or "describe_section"
    min_chars = length_target.get("min_chars")
    max_chars = length_target.get("max_chars")
    avg_sentences = length_target.get("avg_sentences") or ""

    style_samples: List[str] = []
    for chunk in style_chunks[:5]:
        snippet = (chunk.get("text", "") or "")[:700]
        style_samples.append(snippet)
    bullets_allowed = detect_bullets(style_samples)

    parts: List[str] = []
    parts.append("You are an engineering documentation writer. Match the company's tone. Do not invent facts.")
    parts.append("Only use provided facts. If a value is missing, use [TBD].\n")
    parts.append(f"Task: Draft a {section_type} for a {doc_type}. Function: {engineering_function}.")
    if min_chars and max_chars:
        parts.append(f"Length: {min_chars}–{max_chars} characters. Typical sentences: {avg_sentences}.\n")

    if style_samples:
        parts.append("Style exemplars (do NOT copy verbatim; mirror tone and sentence structure):")
        for sample in style_samples:
            parts.append(f"- \"{sample}\"")
        parts.append("")

    if content_chunks:
        parts.append("Facts (use for grounding; cite with [C#]):")
        for idx, chunk in enumerate(content_chunks[:10], 1):
            meta = chunk.get("metadata", {})
            heading = meta.get("heading") or meta.get("section_type") or "Unknown"
            text = (chunk.get("text", "") or "")[:500]
            parts.append(f"[C{idx}] {heading}: {text}")
        parts.append("")

    parts.append("Hard rules:")
    parts.append("- Plain text only.")
    if min_chars and max_chars:
        parts.append(f"- Keep between {min_chars} and {max_chars} characters.")
    if bullets_allowed:
        parts.append("- Bullets allowed if it matches exemplars.")
    else:
        parts.append("- No bullet points.")
    parts.append("- Third-person professional tone.")
    parts.append("- No new facts beyond the provided content.")
    parts.append("- Cite with [C#] where relevant.")
    parts.append("\nWrite the section now.")
    return "\n".join(parts)
