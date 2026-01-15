# SYSTEM_OVERVIEW.md

## 1) High-Level Architecture
- **Two-world model**
  - **Web/Backend (brain):** Ingests artifacts, parses and chunks documents, generates embeddings, stores vectors/metadata, runs retrieval and RAG-based generation.
  - **Desktop Agent (hands):** Syncs local files to the backend and executes user/agent commands (open Word/Excel, file ops). It does not make planning or generation decisions.
- **Artifacts and versions**
  - Every file becomes an **artifact** with a stable `artifact_id`.
  - Each ingest run produces a `version_id` tied to the artifact.
  - Chunks (content/style) are scoped by both `artifact_id` and `version_id` to preserve provenance.

## 2) Data Model
- **Artifacts**
  - Identity: `artifact_id`, `version_id`
  - File info: `file_name`, `file_path`, `file_size`
  - Classification: `doc_type`, `project_name`, `author`
- **Chunks**
  - Identity: `chunk_id`, `artifact_id`, `version_id`, `company_id`
  - Classification: `doc_type`, `section_type`, `chunk_type` (content|style), `calculation_type`
  - Text features: `text`, `normalized_text`, `heading`, `page_number`, `format_hint`, length metrics (chars/words/sentences/paragraphs), section-level aggregates
  - Quality signals: `style_frequency`, `quality_score`, `is_pinned`
- **Content vs Style**
  - **Content chunks:** factual grounding for answers.
  - **Style chunks:** curated exemplars of tone/structure; filtered by `StyleExemplarFilter` (quality + frequency gating). Style chunks may contain factual statements, but are used only to guide tone and structure; content chunks are the authoritative source for factual grounding.

## 3) Tier 1: Ingestion & Retrieval
- **Parsing**
  - DOCX via `python-docx`; PDF via PyMuPDF.
  - Extracts sections, headings, pages, and basic metadata; generates `artifact_id`/`version_id`.
- **Chunking strategy**
  - Section-aware splitting; page-aware for PDFs; overlapping windows where needed.
  - Classify each chunk as content vs style using `StyleExemplarFilter` (quality and duplication frequency).
- **Embeddings lifecycle**
  - Generated **only during ingestion** (never at generation time).
  - Uses OpenAI/local/fallback deterministic embeddings; optional Redis cache.
- **Vector storage**
  - Logical dual indices implemented via `chunk_type`/`index_type` filters (content vs style); may be backed by separate collections or a shared table depending on the VectorStore adapter (Supabase/Qdrant/CSV).
- **Retrieval logic**
  - Filters include `company_id`, `index_type`, optional `doc_type` and `section_type`.
  - Falls back from (section+doc) → (doc) → (company) to avoid empty results.
- **Why embeddings are NOT created in Tier 2**
  - Keeps generation fast, deterministic, and provenance-aligned; avoids mutating the index from the generation path.

## 4) Tier 2: RAG Generation
- **Query analysis**
  - Rules-based `QueryAnalyzer` infers `doc_type`, `section_type`, `engineering_function`, and constraints (calc type, code refs).
- **Section profiling**
  - `SectionProfileLoader` pulls avg/min/max chars (or defaults) per section to set length bounds.
- **Retrieval (content vs style)**
  - Two retrieval passes: content chunks for facts; style chunks for voice.
  - Same fallback pattern (section → doc → company).
- **Prompt construction**
  - `rag_prompt.build_prompt`: embeds style exemplars, labeled content facts `[C#]`, length targets, and hard rules (no new facts, [TBD] if missing, bullet policy based on exemplars).
- **LLM call**
  - `LLMClient` (OpenAI; default `gpt-4o-mini`, requires `OPENAI_API_KEY`).
- **Length enforcement**
  - One rewrite pass if outside target min/max; no second check. This is a deliberate soft constraint to avoid over-editing; can be tightened later.
- **Citations**
  - Returned as chunk metadata (artifact/version/heading/page/score) for traceability.
- **Why hallucinations are “bounded” but not eliminated**
  - Model is instructed to stick to `[C#]` facts, but retrieval is the only guard; no runtime fact-check or strict refusal path.

## 5) Multi-Section Report Generation
- **Section order**
  - Template-driven when available; otherwise inferred from section profiles; fallback to defaults. Inferred section order is heuristic and depends on section labeling quality; template tables are the only deterministic mechanism.
- **Template → inferred → default**
  - Uses section metadata lengths/ordering when present; else defaults.
- **Hybrid vs strict policy**
  - Intro/scope/methodology: template-safe allowed when grounding is missing.
  - Findings/results/recommendations: strict grounding required; otherwise [TBD]/skip.
- **No single-section collapse**
  - Each section retrieved and drafted independently to preserve structure and per-section citations.

## 6) Example End-to-End Flow (methodology generation)
- User prompt: “Draft the methodology section for a structural beam design report referencing ACI 318-19 load combinations and moisture protection details.”
- Analyzer: `doc_type=design_report`, `section_type=methodology`, `engineering_function=describe_section`.
- Retrieval: Supabase content/style chunks; top hits discussed moisture, roof joints, cracking (no ACI load combos present).
- Prompt: Style snippets + factual snippets labeled `[C1..]`, rules (no new facts, [TBD] if missing), target length ~500–900 chars.
- LLM: OpenAI generates text grounded in retrieved moisture/cracking facts (no ACI mention due to missing evidence).
- Output: Draft text + citations list; appended to `info_retrieval/data/drafted_sections.csv` with request, doc/section, length, citations_json.

## 7) What the System DOES WELL
- Clear artifact/version identity and dual indices for content vs style.
- Robust ingestion (DOCX/PDF), section-aware chunking, and metadata ledger.
- Retrieval-first generation with explicit citations.
- Length-aware drafting and style mirroring via exemplars.
- Fallback retrieval to reduce hard failures; CSV audit trail for every draft.

## 8) Known Limitations (IMPORTANT)
- Sparse/ambiguous `section_type` labels reduce targeted retrieval.
- Style index sparsity: few high-quality style chunks → weaker voice mimicry.
- Generic output when retrieval is weak; model may omit requested codes/standards if not ingested.
- No Word/formatting output; plain text only.
- No code-specific grounding unless those clauses are ingested as chunks.
- Length enforcement is soft (single rewrite; can exceed max slightly).
- No hard hallucination guard beyond “use provided facts” instruction.

## 9) How to Improve the System (SAFE ROADMAP)
- Better `section_type` classification during ingestion; enrich rules/model-assisted tagging.
- Add `document_templates` and `section_templates` tables; surface template-driven ordering/lengths.
- Phrase-bank injection for common code/standards boilerplate (tagged as style/content for retrieval).
- Increase curated style exemplars and pin high-quality ones.
- Optional LoRA later for style if RAG/style exemplars remain insufficient (after data quality is solid).
- Tighten length enforcement (multi-pass or truncation with guardrails).
- Desktop agent integration for round-trip edits and user-in-the-loop approvals.

## 10) What NOT to Do
- Do not generate without grounding chunks; avoid “empty retrieval” freeform generations.
- Do not embed during generation; embeddings belong to ingestion only.
- Do not mix formatting concerns (Word layout) into content logic; keep generation plain text.
- Do not skip artifact/version identity when storing or citing chunks.
