-- Supabase / Postgres SQL editor helpers for the info_retrieval vector tables.
-- Use in the Supabase SQL editor. Run in a safe environment before production.

-- ================================
-- Drop tables (DANGER)
-- ================================
-- Drop the vector table and metadata tables. This deletes all embeddings.
-- Uncomment to execute.
-- DROP TABLE IF EXISTS chunks CASCADE;
-- DROP TABLE IF EXISTS documents CASCADE;

-- ================================
-- Alter chunks table (add/remove columns)
-- ================================
-- Add template/session linkage columns and doc_type variant.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS template_id TEXT;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS section_id TEXT;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS doc_type_variant TEXT;

-- Optional: constrain chunk_type to known values (extend when adding new types).
-- ALTER TABLE chunks
--   ADD CONSTRAINT chunk_type_allowed
--   CHECK (chunk_type IN ('content', 'style', 'section_intro', 'section_outro', 'section_transition', 'style_exemplar'));

-- Indexes for new columns.
CREATE INDEX IF NOT EXISTS idx_chunks_template_id ON chunks(template_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section_id ON chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_type_variant ON chunks(doc_type_variant);

-- Drop columns (safe on Postgres; ensure nothing references these first).
-- ALTER TABLE chunks DROP COLUMN IF EXISTS template_id;
-- ALTER TABLE chunks DROP COLUMN IF EXISTS section_id;
-- ALTER TABLE chunks DROP COLUMN IF EXISTS doc_type_variant;

-- ================================
-- Inspect schema
-- ================================
-- View table definition.
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'chunks'
-- ORDER BY ordinal_position;

-- Check indexes.
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'chunks';

