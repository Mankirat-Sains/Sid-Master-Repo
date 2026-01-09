# Engineering Document AI System – Tier 1 (RAG Foundation)

This package provides a retrieval-first foundation for engineering documents with dual vector indexes (content vs. style), rules-based metadata extraction, and artifact/version identity baked into the schema.

## Key Capabilities
- Parse `.docx` and `.pdf` (PyMuPDF) into structured sections, pages, and tables.
- Smart chunking (section-aware, overlapping windows, PDF page-aware).
- Chunk classification into `content` vs `style` collections for dual-index retrieval.
- Rules-based metadata extraction with pluggable classifiers and artifact/version identity.
- Embedding generation via OpenAI, local sentence-transformers, or deterministic fallback.
- Storage with Qdrant (or in-memory) and SQLite metadata ledger.
- Retrieval APIs for content queries and style exemplars.

## Quickstart
```bash
cd info_retrieval
python -m venv venv
source venv/bin/activate  # on Windows use venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # set keys/paths
# optional: start infra
docker-compose up -d
# run tests
pytest -q info_retrieval/tests
# run demo (requires sample doc at info_retrieval/data/sample_docs/thermal_calculation.docx)
python -m info_retrieval.demo
```

## Core Modules
- `src/ingest/document_parser.py`: DOCX/PDF parsing, section inference, artifact/version IDs.
- `src/ingest/chunking.py`: Section-based, overlapping, and PDF page chunking; chunk type classification.
- `src/ingest/metadata_extractor.py`: `MetadataExtractor` with rules-based classifier (pluggable).
- `src/embeddings/embedding_service.py`: Embedding abstraction (OpenAI/local/fallback).
- `src/storage/vector_store.py`: Backend-agnostic VectorStore interface.
- `src/storage/qdrant_vector_store.py`: Qdrant adapter implementing VectorStore.
- `src/storage/supabase_vector_store.py`: Supabase adapter implementing VectorStore (uses RPC/table).
- `src/storage/vector_db.py`: Legacy Qdrant helper used by the Qdrant adapter.
- `src/storage/metadata_db.py`: SQLite chunk metadata schema with identity + provenance.
- `src/retrieval/retriever.py`: High-level retrieval for content queries and style exemplars.
- `src/utils/config.py`: Env/config loader; `logger.py`: logging helper.
- `src/ingest/pipeline.py`: Orchestrates parse → chunk → classify → embed → store.
- `src/ingest/style_filter.py`: Quality gating for style exemplars.

## Usage Sketch
```python
from ingest.document_parser import parse_docx
from ingest.chunking import smart_chunk, tag_chunks_with_type
from ingest.metadata_extractor import MetadataExtractor, RulesBasedClassifier
from embeddings.embedding_service import EmbeddingService
from storage.vector_db import VectorDB
from retrieval.retriever import Retriever
from utils.config import load_config

config = load_config()
doc = parse_docx("data/sample_docs/example.docx", company_id="acme", source="upload")
chunks = tag_chunks_with_type(smart_chunk(doc), {"section_types": {s.title: "general" for s in doc.sections}})

metadata_extractor = MetadataExtractor(RulesBasedClassifier())
doc_meta = metadata_extractor.extract_metadata(doc, company_id="acme")
chunk_metadata = [
    {
        **doc_meta,
        "chunk_id": f"{doc_meta['artifact_id']}_{idx}",
        "chunk_type": chunk["chunk_type"],
        "section_type": doc_meta["section_types"].get(chunk.get("section_title")),
        "text": chunk["text"],
        "heading": chunk.get("section_title"),
    }
    for idx, chunk in enumerate(chunks)
]

embedding_service = EmbeddingService(config)
vector_db = VectorDB(config, use_in_memory=True)
retriever = Retriever(embedding_service, vector_db)
retriever.index_chunks(chunks, chunk_metadata, company_id="acme")
results = retriever.retrieve_content("foundation design", company_id="acme", top_k=3)
```

## Notes
- PDFs use PyMuPDF for layout-aware extraction; prefer section/page-aware chunking for long reports.
- Dual-index collections are created per company to avoid migrations when style retrieval is added.
- Artifact/version identity is mandatory for desktop agent integrations and audit trails.

## Next Steps
- Wire metadata DB into ingestion flow.
- Add LLM-backed classifier (fallback) and richer PDF table extraction.
- Add CLI/notebook walkthrough for full end-to-end ingestion.
