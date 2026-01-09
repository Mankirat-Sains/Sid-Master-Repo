from __future__ import annotations

from typing import Dict, List, Optional

from ..utils.logger import get_logger
from .document_parser import ParsedDocument, Section

logger = get_logger(__name__)


def chunk_by_section(document: ParsedDocument) -> List[Dict[str, object]]:
    """
    Chunk a document so each section is its own chunk.
    """
    chunks: List[Dict[str, object]] = []
    for section in document.sections or []:
        if not section.content.strip():
            continue
        chunks.append(
            {
                "text": section.content.strip(),
                "section_title": section.title,
                "level": section.level,
            }
        )
    if not chunks and document.text:
        logger.warning("No explicit sections found; returning a single chunk.")
        chunks.append({"text": document.text.strip(), "section_title": "full_document", "level": 1})
    return chunks


def chunk_with_overlap(text: str, size: int = 512, overlap: int = 50) -> List[str]:
    """
    Sliding window chunking that overlaps by `overlap` tokens.
    Tokens are approximated by whitespace-delimited words for speed.
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive.")

    words = text.split()
    if not words:
        return []

    step = max(size - overlap, 1)
    chunks: List[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            continue
        chunks.append(" ".join(window))
        if start + size >= len(words):
            break
    return chunks


def smart_chunk(document: ParsedDocument, max_tokens: int = 512) -> List[Dict[str, object]]:
    """
    Adaptive chunking: use sections when small, otherwise split large sections with overlap.
    """
    chunks: List[Dict[str, object]] = []
    for section in document.sections or [Section(title="full_document", content=document.text)]:
        token_estimate = _approximate_tokens(section.content)
        if token_estimate <= max_tokens:
            chunks.append(
                {
                    "text": section.content.strip(),
                    "section_title": section.title,
                    "level": section.level,
                }
            )
        else:
            split_chunks = chunk_with_overlap(section.content, size=max_tokens, overlap=round(max_tokens * 0.1))
            for idx, chunk_text in enumerate(split_chunks):
                chunks.append(
                    {
                        "text": chunk_text,
                        "section_title": f"{section.title} (part {idx + 1})",
                        "level": section.level,
                    }
                )
    return chunks


def chunk_pdf_pages(document: ParsedDocument, max_tokens: int = 512) -> List[Dict[str, object]]:
    """
    Chunk PDFs using page boundaries with optional overlap for long pages.
    """
    if not document.pages:
        return smart_chunk(document, max_tokens=max_tokens)

    chunks: List[Dict[str, object]] = []
    for page in document.pages:
        text = page.get("text", "") or ""
        if not text.strip():
            continue
        token_estimate = _approximate_tokens(text)
        if token_estimate <= max_tokens:
            chunks.append(
                {
                    "text": text.strip(),
                    "section_title": f"Page {page.get('page_number')}",
                    "level": 1,
                    "page_number": page.get("page_number"),
                }
            )
        else:
            split_chunks = chunk_with_overlap(text, size=max_tokens, overlap=round(max_tokens * 0.1))
            for idx, chunk_text in enumerate(split_chunks):
                chunks.append(
                    {
                        "text": chunk_text,
                        "section_title": f"Page {page.get('page_number')} (part {idx + 1})",
                        "level": 1,
                        "page_number": page.get("page_number"),
                    }
                )
    return chunks


def classify_chunk_type(chunk: Dict[str, object], metadata: Optional[Dict[str, object]] = None) -> str:
    """
    Determine if a chunk should be routed to content or style collection.
    """
    text = str(chunk.get("text", "")).lower()
    section_title = str(chunk.get("section_title", "")).lower()
    meta = metadata or {}
    section_type = meta.get("section_type")
    if not section_type and isinstance(meta.get("section_types"), dict):
        section_type = meta["section_types"].get(chunk.get("section_title"))

    content_keywords = ["calculation", "result", "table", "specification", "load", "kpa", "kN", "pressure"]
    style_keywords = ["introduction", "methodology", "background", "scope", "conclusion", "summary", "purpose"]

    if any(keyword.lower() in text for keyword in content_keywords):
        return "content"
    if any(keyword.lower() in section_title for keyword in content_keywords):
        return "content"
    if any(keyword.lower() in text for keyword in style_keywords):
        return "style"
    if section_type in {"introduction", "methodology", "conclusions"}:
        return "style"
    return "content"


def tag_chunks_with_type(chunks: List[Dict[str, object]], metadata: Optional[Dict[str, object]] = None) -> List[Dict[str, object]]:
    """
    Attach chunk_type to each chunk based on heuristics.
    """
    for chunk in chunks:
        chunk["chunk_type"] = classify_chunk_type(chunk, metadata)
    return chunks


def _approximate_tokens(text: str) -> int:
    """
    Approximate token count using word count; sufficient for chunk sizing.
    """
    return len(text.split())
