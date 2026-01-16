# Docgen Revamp Progress Log

## What we changed
- Created new template structure tables in Postgres/Supabase:
  - `document_templates` (added `template_id` unique, `metadata` holds heading_style/default_format/schema_version, `template_name` set to “<doc_type> template v1” where missing).
  - `template_sections` (FK to `document_templates.template_id`; sections expanded from legacy `section_order`; indexed by `template_id, position_order`).
- Migrated legacy `document_templates` data:
  - Moved `heading_style`, `default_format`, `schema_version` into `metadata`.
  - Expanded `section_order` arrays into ordered rows in `template_sections`.
  - Dropped legacy columns `section_order`, `heading_style`, `default_format`.
- Added new columns for revamp linkage:
  - Supabase `chunks`: `template_id`, `section_id`, `doc_type_variant` + indexes.
  - SQLite `documents`/`chunks`: `template_id`, `session_id` (documents); `template_id`, `section_id` (chunks) + indexes.
- Verified data:
  - `document_templates` now contains entries like `design_report template v1`, `calculation_narrative template v1`, `method_statement template v1` with heading styles in `metadata`.
  - `template_sections` populated with ordered sections per template (e.g., executive_summary → references for design_report).

## Reference queries
- Fetch template + ordered sections (asyncpg example):
  - See DAO sketch in chat: selects active template by `company_id`, `doc_type`, joins `template_sections` ordered by `position_order`, returns metadata + sections list.

## What’s next
- Wire docgen planner to pull structure from `template_sections` and heading/defaults from `document_templates.metadata`.
- Add feature flag to drive section-by-section generation; keep legacy flow as fallback.
- Update ingestion/retrieval to tolerate new `chunk_type` values and passthrough columns (`template_id`, `section_id`, `doc_type_variant`).
- Implement section-level approval flow (interrupts + `/approve-section`) backed by new tables.
- Add migrations/runner scripts to automate the above in CI/deploy.
