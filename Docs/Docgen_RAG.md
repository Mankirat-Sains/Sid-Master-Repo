# Doc Generation RAG Flow

This note explains how the doc generation path works today: how requests are routed, what data stores power grounding, how drafts are produced, and how DOCX output is materialized for the UI.

## Routing and state
- The parent graph (`Backend/graph/builder.py`) always runs `doc_task_classifier` after the plan. If `workflow=docgen` or `task_type` is `doc_section`/`doc_report` (or `requires_desktop_action`/desktop tools are set), the request is routed to the desktop/docgen subgraph.
- The docgen subgraph (`Backend/graph/subgraphs/desktop/docgen_subgraph.py`) does lightweight routing: optional retrieval guard → plan → section/report generation → answer adaptation → verify/correct. It normalizes state to/from `RAGState` so downstream nodes still see `doc_generation_result`, `doc_generation_warnings`, `final_answer`, `conversation_history`, etc.
- In deep-agent mode, the desktop loop (`Backend/nodes/DesktopAgent/deep_desktop_loop.py`) short-circuits doc workflows to a single `generate_document` tool call so docgen still runs, but now inside a workspace with eviction/interrupt safety. The tool wrapper lives in `Backend/nodes/DesktopAgent/tools/docgen_tool.py`.

## Data stores used for grounding
- **Vector store (primary):** Supabase via `SupabaseVectorStore` (`Local Agent/info_retrieval/src/storage/supabase_vector_store.py`). Chunks are stored in a table (default `chunks`) with columns `id`, `content`, `embedding`, optional `metadata`, plus passthrough columns: `artifact_id`, `version_id`, `company_id`, `chunk_type`/`index_type` (content vs style), `section_type`, `doc_type`, `source`, `file_path`, `heading`, `page_number`. Similarity search is via RPC (default `match_chunks`) with filters mapped to `company_filter`, `index_type_filter`, `section_type_filter`, etc.
- **Local metadata DB:** SQLite wrapper (`Local Agent/info_retrieval/src/storage/metadata_db.py`) seeded at `config.metadata_db_path`. Tables:
  - `documents(artifact_id PK, company_id, file_name, file_path, file_size, latest_version_id, doc_type, project_name, author, created_at, schema_version)`
  - `chunks(chunk_id PK, artifact_id FK, version_id, company_id, source, file_path, doc_type, section_type, chunk_type, calculation_type, text, normalized_text, style_frequency, quality_score, is_pinned, page_number, section_number, heading, project_name, author, reviewer, tags JSON, parent_artifact_id, related_chunks JSON, created_at, modified_at, schema_version)` with indexes on artifact/company/doc_type/section_type/created/normalized_text.
  - Used for section-length profiling (`SectionProfileLoader`) and style frequency lookups.
- **Embeddings:** `EmbeddingService` embeds queries/chunks; vectors are stored only in the vector table (Supabase or in-memory Qdrant fallback).

## Retrieval & grounding
- The Tier2 generator (`Local Agent/info_retrieval/src/tier2/generator.py`) orchestrates retrieval and drafting.
- For each request it:
  1) Runs `QueryAnalyzer` to infer `doc_type`/`section_type`.
  2) Loads length targets from `SectionProfileLoader` (metadata DB) for the company/doc/section; defaults to section-type heuristics when stats are missing.
  3) Retrieves **content** chunks (top_k=10) and **style** chunks (top_k=4) via `Retriever.retrieve_for_query`. Filters widen progressively: company+chunk_type+doc_type+section_type → company+chunk_type+doc_type → company+chunk_type. Scores/preview logged.
  4) Merges pre-fetched graded/retrieved docs from state (`extra_context`) so downstream sections can be grounded on earlier retrieval results.
- Retrieval outputs are converted to formatted context strings and citation objects (`artifact_id`, `source/file_path`, `page_number`, `chunk_id`, `score`), then deduped by base document.

## Drafting logic
- Generation modes depend on retrieval quality:
  - **retrieved:** ≥3 chunks and top score ≥0.6 → fully grounded draft.
  - **hybrid:** some chunks with score ≥0.4 → mix evidence + industry guidance, warns about limited grounding.
  - **general:** no usable chunks → industry-standard guidance only, warns that KB lacked matches.
- Prompts include style cues from style chunks and enforce section length (min/max chars derived from section profiles). A rewrite pass enforces length if needed.
- Guardrails: strip `[TBD]`/warning banners and inline citation brackets; fall back to CSV templates (`Local Agent/info_retrieval/data/drafted_sections.csv`) or a canned paragraph when grounding is empty. Citations metadata is always attached for UI dropdowns.

## Outputs and state fields
- Generation nodes return `doc_generation_result` with `draft_text`, optional `combined_text`/`sections`, `citations`, `citations_metadata` (documents + warnings + search metadata), `length_target`, `warnings`, and `debug` about retrieval counts/mode.
- `doc_generation_warnings` is surfaced alongside `final_answer`/`answer_citations` and merged into `conversation_history` by `doc_correct`.
- Deep-agent tool path may evict large drafts: content beyond `MAX_INLINE_TOOL_RESULT` is written to the workspace with a summary; payload includes `eviction` metadata and, if successful, `doc_generation_result` mirrors the inline output (cleaned).

## DOCX materialization
- The API layer (`Backend/api_server.py`) decides when to build a DOCX (`should_materialize_doc`) and renders via `materialize_onlyoffice_document`:
  - Cleans TBD/warning noise, normalizes blocks (`draft_text` → paragraphs; `sections` → heading+paragraph blocks; supports lists/tables).
  - Writes a DOCX using python-docx (`render_docx_to_file`), stores it under `/documents/{session}.docx`, and returns a `document_state` payload (OnlyOffice URL/key, sections/blocks) for the frontend preview.
  - If no structured result is present, falls back to `answer_text`.
- Frontend (`Frontend/Frontend/components/DocumentPreviewPanel.vue` via `useDocumentWorkflow`) opens the document pane when workflow/task_type indicates docgen and uses the `document_state` payload for live preview/editing.

## End-to-end summary
1) User asks for a doc/section → classifier sets `workflow=docgen`/`task_type`.
2) Subgraph/planner builds `doc_request`; optional desktop plan is attached if user asked to handle files.
3) Tier2 generator retrieves content/style chunks from Supabase (or Qdrant fallback) using embeddings + filters, with metadata DB providing length/style hints.
4) Draft is produced with grounded citations; text is sanitized and packed into `doc_generation_result` (+ warnings/metadata).
5) API streams the answer; if docgen is detected it also materializes DOCX for OnlyOffice and returns `document_state`.
6) Deep-agent path (when enabled) wraps the same generator as a tool, adds workspace context, evicts large drafts, and respects interrupt gating for destructive desktop actions.
