# Docgen Revamp Progress Log

## What we changed
- Created new template structure tables in Postgres/Supabase:
  - `document_templates` (added stable `template_id` unique, `template_name`/`version`/`is_active`, `metadata` holds heading_style/default_format/schema_version).
  - `template_sections` (FK to `document_templates.template_id`; backfilled from legacy `section_order`; indexed by `template_id, position_order`).
- Migrated legacy `document_templates` data:
  - Backfilled template metadata and IDs (guarded for environments without legacy columns).
  - Expanded `section_order` arrays into ordered rows in `template_sections` where available.
- Added new columns for revamp linkage:
  - Supabase `chunks`: `template_id`, `section_id`, `doc_type_variant` + indexes.
  - SQLite `documents`/`chunks`: `template_id`, `session_id` (documents); `template_id`, `section_id` (chunks) + indexes.
- Verified data:
  - `document_templates` now contains entries like `design_report template v1`, `calculation_narrative template v1`, `method_statement template v1` with heading styles in `metadata`.
  - `template_sections` populated with ordered sections per template (e.g., executive_summary → references for design_report).
- Ingestion/resolution:
  - Ingestion pipeline auto-resolves `template_id` and `section_id` mapping from Supabase templates/sections (if not supplied) and stamps them (plus `doc_type_variant`) into chunk metadata.
  - Supabase vector store passthrough/mapping updated for `template_id`/`section_id`/`doc_type_variant`.
- Generation:
  - Report and section generators honor `SECTION_BY_SECTION_GENERATION` (with optional allowlist), fetch template sections from Supabase, and pass `template_id`/`section_id`/`template_sections`/`doc_type_variant` into drafts and results.
- Migrations:
  - Apply in order: `001_create_document_templates.sql`, `002_create_section_templates.sql`, `003_create_style_rules.sql`, `004_template_sections.sql` (adds stable template_id, template metadata, template_sections backfill).

## Reference queries
- Fetch template + ordered sections (asyncpg example):
  - See DAO sketch in chat: selects active template by `company_id`, `doc_type`, joins `template_sections` ordered by `position_order`, returns metadata + sections list.

## What’s next
- Implement section-level approval flow (interrupts + `/approve-section`) backed by new tables.
- Harden CI migration runner to include 004 in deploy pipelines.
