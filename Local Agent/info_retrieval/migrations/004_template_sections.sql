-- Migration: 004_template_sections.sql
-- Purpose: Add stable template identifiers and a first-class template_sections catalog
-- Notes:
--   - Compatible with Supabase/Postgres (uses gen_random_uuid, jsonb)
--   - Backfills template_id and template metadata for existing rows
--   - Expands legacy section_order arrays into ordered template_sections rows

-- 1) Extend document_templates with template metadata and stable IDs
ALTER TABLE document_templates
    ADD COLUMN IF NOT EXISTS template_id UUID DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS template_name TEXT,
    ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Backfill template_id, template_name, and metadata from legacy fields (guarded for missing columns)
DO $$
DECLARE
    hs_exists BOOLEAN;
    df_exists BOOLEAN;
    sv_exists BOOLEAN;
    stmt TEXT;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_templates' AND column_name = 'heading_style'
    ) INTO hs_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_templates' AND column_name = 'default_format'
    ) INTO df_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_templates' AND column_name = 'schema_version'
    ) INTO sv_exists;

    stmt := 'UPDATE document_templates
             SET
                 template_id = COALESCE(template_id, id, gen_random_uuid()),
                 template_name = COALESCE(template_name, CONCAT(doc_type, '' template v'', COALESCE(version, 1))),
                 version = COALESCE(version, 1),
                 is_active = COALESCE(is_active, TRUE),
                 metadata = COALESCE(metadata, ''{}''::jsonb)';

    IF hs_exists THEN
        stmt := stmt || ' || jsonb_build_object(''heading_style'', heading_style)';
    END IF;
    IF df_exists THEN
        stmt := stmt || ' || jsonb_build_object(''default_format'', default_format)';
    END IF;
    IF sv_exists THEN
        stmt := stmt || ' || jsonb_build_object(''schema_version'', schema_version)';
    END IF;

    stmt := stmt || ' WHERE template_id IS NULL
                       OR template_name IS NULL
                       OR metadata IS NULL
                       OR metadata = ''{}''::jsonb;';

    EXECUTE stmt;
END $$;

-- Enforce uniqueness and not-null on the new identifiers
ALTER TABLE document_templates ALTER COLUMN template_id SET NOT NULL;
ALTER TABLE document_templates ALTER COLUMN template_name SET NOT NULL;
ALTER TABLE document_templates ALTER COLUMN version SET NOT NULL;
ALTER TABLE document_templates ALTER COLUMN is_active SET NOT NULL;

ALTER TABLE document_templates
    ADD CONSTRAINT document_templates_template_id_unique UNIQUE (template_id);

-- Ensure each company/doc_type/version combination is unique
ALTER TABLE document_templates
    ADD CONSTRAINT document_templates_company_doc_version UNIQUE (company_id, doc_type, version);

-- 2) Create template_sections table to materialize ordered sections per template
CREATE TABLE IF NOT EXISTS template_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES document_templates(template_id),
    section_type TEXT NOT NULL,
    section_name TEXT,
    position_order INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    is_optional BOOLEAN DEFAULT FALSE,
    min_length_chars INTEGER,
    max_length_chars INTEGER,
    typical_length_chars INTEGER,
    style_guidelines JSONB,
    heading_level INTEGER,
    section_prompt_template TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT template_sections_unique_section UNIQUE (template_id, section_type),
    CONSTRAINT template_sections_unique_position UNIQUE (template_id, position_order)
);

CREATE INDEX IF NOT EXISTS idx_template_sections_template ON template_sections(template_id);
CREATE INDEX IF NOT EXISTS idx_template_sections_order ON template_sections(template_id, position_order);

-- 3) Backfill template_sections from legacy section_order arrays (only if the column exists)
DO $$
DECLARE
    so_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_templates' AND column_name = 'section_order'
    ) INTO so_exists;

    IF so_exists THEN
        INSERT INTO template_sections (
            template_id,
            section_type,
            section_name,
            position_order,
            is_required,
            is_optional,
            metadata
        )
        SELECT
            dt.template_id,
            elem::text AS section_type,
            INITCAP(REPLACE(elem::text, '_', ' ')) AS section_name,
            ord AS position_order,
            TRUE AS is_required,
            FALSE AS is_optional,
            '{}'::jsonb AS metadata
        FROM document_templates dt
        CROSS JOIN LATERAL jsonb_array_elements(dt.section_order) WITH ORDINALITY AS t(elem, ord)
        WHERE dt.section_order IS NOT NULL
          AND jsonb_typeof(dt.section_order) = 'array'
        ON CONFLICT (template_id, section_type) DO NOTHING;
    END IF;
END $$;
