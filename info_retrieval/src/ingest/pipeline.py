"""
End-to-end ingestion pipeline: parse -> metadata -> chunk -> classify -> embed -> store.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List

from embeddings.embedding_service import EmbeddingService
from storage.metadata_db import MetadataDB
from storage.vector_store import Chunk, VectorStore
from utils.logger import get_logger
from .chunking import chunk_pdf_pages, smart_chunk
from .document_parser import parse_docx, parse_pdf
from .metadata_extractor import MetadataExtractor
from .style_filter import StyleExemplarFilter

logger = get_logger(__name__)


def _length_metrics(text: str) -> Dict[str, int | str]:
    paragraphs = [p for p in text.splitlines() if p.strip()]
    sentence_count = len(re.findall(r"[.!?]", text))
    return {
        "length_chars": len(text),
        "length_words": len(text.split()),
        "paragraph_count": len(paragraphs),
        "sentence_count": sentence_count,
    }


class IngestionPipeline:
    """
    Coordinates document ingestion into dual indices and metadata DB.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        metadata_db: MetadataDB,
        company_id: str,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.metadata_db = metadata_db
        self.company_id = company_id
        self.metadata_extractor = MetadataExtractor()
        self.style_filter = StyleExemplarFilter()

    def ingest(self, file_path: str) -> Dict[str, int | str]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() == ".pdf":
            parsed = parse_pdf(path, company_id=self.company_id)
            chunks = chunk_pdf_pages(parsed)
        else:
            parsed = parse_docx(path, company_id=self.company_id)
            chunks = smart_chunk(parsed)

        # Pre-compute section-level length metrics so every chunk carries its parent section stats.
        section_stats: Dict[str, Dict[str, int]] = {}
        if parsed.sections:
            for section in parsed.sections:
                section_stats[section.title] = _length_metrics(section.content)
        else:
            # Fallback: aggregate by chunk section title
            for chunk in chunks:
                title = chunk.get("section_title") or "unknown"
                existing = section_stats.get(title, {"length_chars": 0, "length_words": 0, "paragraph_count": 0, "sentence_count": 0})
                metrics = _length_metrics(chunk.get("text", ""))
                section_stats[title] = {
                    "length_chars": existing["length_chars"] + metrics["length_chars"],
                    "length_words": existing["length_words"] + metrics["length_words"],
                    "paragraph_count": existing["paragraph_count"] + metrics["paragraph_count"],
                    "sentence_count": existing["sentence_count"] + metrics["sentence_count"],
                }

        doc_meta = self.metadata_extractor.extract_metadata(parsed, company_id=self.company_id)
        self.metadata_db.insert_document(
            {
                "artifact_id": doc_meta["artifact_id"],
                "company_id": self.company_id,
                "file_name": path.name,
                "file_path": str(path),
                "file_size": path.stat().st_size if path.exists() else None,
                "latest_version_id": doc_meta["version_id"],
                "doc_type": doc_meta.get("doc_type"),
                "project_name": doc_meta.get("project_name"),
                "author": doc_meta.get("author"),
            }
        )

        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        if not embeddings:
            logger.warning("No embeddings generated for %s", file_path)
            return {"artifact_id": doc_meta["artifact_id"], "version_id": doc_meta["version_id"], "chunk_count": 0}

        chunk_records: List[Chunk] = []
        content_count = 0
        style_count = 0
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_meta['artifact_id']}_{idx}"
            section_type = doc_meta.get("section_types", {}).get(chunk.get("section_title"))
            text = chunk.get("text", "")
            normalized_text = self.style_filter._normalize(text)
            frequency_before = self.metadata_db.get_style_frequency(normalized_text, section_type)
            quality_score = self.style_filter.compute_quality_score(text)
            text_length_chars = len(text)
            text_length_words = len(text.split())
            paragraph_count = len([p for p in text.splitlines() if p.strip()])
            sentence_count = len(re.findall(r"[.!?]", text))
            format_hint = "bullet" if any(re.match(r"^\\s*[-*•]\\s", line) for line in text.splitlines()) else "paragraph"
            section_length = section_stats.get(chunk.get("section_title"), {})

            style_meta = {
                "section_type": section_type,
                "heading": chunk.get("section_title"),
                "tags": doc_meta.get("tags", []),
                "chunk_id": chunk_id,
                "style_frequency": frequency_before,
                "quality_score": quality_score,
            }

            chunk_type = "style" if self.style_filter.is_style_exemplar(text, style_meta, quality_score) else "content"
            style_frequency = frequency_before + 1 if chunk_type == "style" else 0
            if chunk_type == "style":
                style_count += 1
            else:
                content_count += 1

            chunk_metadata = {
                "chunk_id": chunk_id,
                "artifact_id": doc_meta["artifact_id"],
                "version_id": doc_meta["version_id"],
                "company_id": self.company_id,
                "source": doc_meta.get("source", "upload"),
                "doc_type": doc_meta.get("doc_type"),
                "section_type": section_type,
                "chunk_type": chunk_type,
                "index_type": chunk_type,
                "calculation_type": doc_meta.get("calculation_type"),
                "text": text,
                "page_number": chunk.get("page_number"),
                "heading": chunk.get("section_title"),
                "schema_version": "1.0",
                "normalized_text": normalized_text,
                "style_frequency": style_frequency,
                "quality_score": quality_score,
                "is_pinned": False,
                "text_length_chars": text_length_chars,
                "text_length_words": text_length_words,
                "paragraph_count": paragraph_count,
                "sentence_count": sentence_count,
                "format_hint": format_hint,
                "section_length_chars": section_length.get("length_chars"),
                "section_length_words": section_length.get("length_words"),
                "section_paragraph_count": section_length.get("paragraph_count"),
                "section_sentence_count": section_length.get("sentence_count"),
            }

            self.metadata_db.insert_chunk_metadata(chunk_metadata)
            chunk_records.append(Chunk(id=chunk_id, text=text, embedding=vector, metadata=chunk_metadata))

        if chunk_records:
            self.vector_store.upsert(chunk_records)

        return {
            "artifact_id": doc_meta["artifact_id"],
            "version_id": doc_meta["version_id"],
            "chunk_count": len(chunks),
            "content_chunks": content_count,
            "style_chunks": style_count,
        }
