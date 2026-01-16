-- SQLite SQL editor helpers for the info_retrieval metadata DB (documents, chunks).
-- Run against a COPY of the DB first; SQLite ALTER support is limited.

-- ================================
-- Drop tables (DANGER)
-- ================================
-- This deletes all metadata rows. Uncomment to execute.
-- DROP TABLE IF EXISTS chunks;
-- DROP TABLE IF EXISTS documents;

-- ================================
-- Add columns (SQLite supports ADD COLUMN only)
-- ================================
-- Linkage to templates/sessions.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS template_id TEXT;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS section_id TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS template_id TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS session_id TEXT;

-- Indexes for new columns.
CREATE INDEX IF NOT EXISTS idx_chunks_template ON chunks(template_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_documents_template ON documents(template_id);
CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);

-- ================================
-- Remove or rename columns (SQLite workaround)
-- ================================
-- SQLite cannot DROP COLUMN directly. To remove/rename:
-- 1) BEGIN TRANSACTION;
-- 2) CREATE TABLE new_chunks AS SELECT <columns you want to keep/rename> FROM chunks;
-- 3) DROP TABLE chunks;
-- 4) ALTER TABLE new_chunks RENAME TO chunks;
-- 5) Recreate indexes/triggers if needed;
-- 6) COMMIT;
--
-- Example skeleton (adjust columns):
-- BEGIN TRANSACTION;
-- CREATE TABLE new_chunks AS
--   SELECT chunk_id, artifact_id, version_id, company_id, source, file_path,
--          doc_type, section_type, chunk_type, calculation_type, text,
--          normalized_text, style_frequency, quality_score, is_pinned,
--          page_number, section_number, heading, project_name, author, reviewer,
--          tags, parent_artifact_id, related_chunks, created_at, modified_at,
--          template_id, section_id
--   FROM chunks;
-- DROP TABLE chunks;
-- ALTER TABLE new_chunks RENAME TO chunks;
-- CREATE INDEX IF NOT EXISTS idx_chunks_template ON chunks(template_id);
-- CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section_id);
-- COMMIT;

-- ================================
-- Inspect schema
-- ================================
-- PRAGMA table_info('chunks');
-- PRAGMA index_list('chunks');
-- PRAGMA table_info('documents');
-- PRAGMA index_list('documents');

