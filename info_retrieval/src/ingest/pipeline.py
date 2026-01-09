"""
End-to-end ingestion pipeline: parse -> metadata -> chunk -> classify -> embed -> store.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from ..embeddings.embedding_service import EmbeddingService
from ..storage.metadata_db import MetadataDB
from ..storage.vector_db import VectorDB
from ..utils.logger import get_logger
from .chunking import chunk_pdf_pages, smart_chunk, tag_chunks_with_type
from .document_parser import parse_docx, parse_pdf
from .metadata_extractor import MetadataExtractor
from .style_filter import StyleExemplarFilter

logger = get_logger(__name__)


class IngestionPipeline:
    """
    Coordinates document ingestion into dual indices and metadata DB.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_db: VectorDB,
        metadata_db: MetadataDB,
        company_id: str,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_db = vector_db
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

        # tag chunk types with style filter info
        tagged_chunks = tag_chunks_with_type(chunks, {**doc_meta, "_style_filter": self.style_filter})

        texts = [c["text"] for c in tagged_chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        if not embeddings:
            logger.warning("No embeddings generated for %s", file_path)
            return {"artifact_id": doc_meta["artifact_id"], "version_id": doc_meta["version_id"], "chunk_count": 0}

        # ensure collections initialized
        self.vector_db.initialize_collections(self.company_id, len(embeddings[0]))

        content_chunks = []
        content_vectors = []
        style_chunks = []
        style_vectors = []

        for idx, (chunk, vector) in enumerate(zip(tagged_chunks, embeddings)):
            chunk_id = f"{doc_meta['artifact_id']}_{idx}"
            chunk_metadata = {
                "chunk_id": chunk_id,
                "artifact_id": doc_meta["artifact_id"],
                "version_id": doc_meta["version_id"],
                "company_id": self.company_id,
                "source": doc_meta.get("source", "upload"),
                "doc_type": doc_meta.get("doc_type"),
                "section_type": doc_meta.get("section_types", {}).get(chunk.get("section_title")),
                "chunk_type": chunk.get("chunk_type", "content"),
                "calculation_type": doc_meta.get("calculation_type"),
                "text": chunk.get("text"),
                "page_number": chunk.get("page_number"),
                "heading": chunk.get("section_title"),
                "schema_version": "1.0",
            }

            if chunk_metadata["chunk_type"] == "style":
                style_chunks.append(chunk_metadata)
                style_vectors.append(vector)
            else:
                content_chunks.append(chunk_metadata)
                content_vectors.append(vector)

            self.metadata_db.insert_chunk_metadata(chunk_metadata)

        if content_chunks:
            self.vector_db.insert_chunks(content_chunks, content_vectors, content_chunks, self.company_id)
        if style_chunks:
            self.vector_db.insert_chunks(style_chunks, style_vectors, style_chunks, self.company_id)

        return {
            "artifact_id": doc_meta["artifact_id"],
            "version_id": doc_meta["version_id"],
            "chunk_count": len(tagged_chunks),
            "content_chunks": len(content_chunks),
            "style_chunks": len(style_chunks),
        }
