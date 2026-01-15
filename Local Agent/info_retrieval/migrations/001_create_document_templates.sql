-- Migration: 001_create_document_templates.sql

CREATE TABLE IF NOT EXISTS document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,

    -- Structure definition
    section_order JSONB NOT NULL,  -- ["introduction", "methodology", ...]
    heading_style JSONB,           -- {"h1": "Heading 1", "h2": "Heading 2"} (optional)
    default_format JSONB,          -- {"bullets": true, "tables": ["results"]} (optional)

    -- Metadata
    schema_version TEXT NOT NULL DEFAULT '1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_company_doc_type UNIQUE(company_id, doc_type)
);

CREATE INDEX IF NOT EXISTS idx_document_templates_company ON document_templates(company_id);
CREATE INDEX IF NOT EXISTS idx_document_templates_doc_type ON document_templates(company_id, doc_type);

-- Seed data for demo
INSERT INTO document_templates (company_id, doc_type, section_order, heading_style) VALUES
('demo_company', 'design_report',
 '["cover_page", "executive_summary", "introduction", "assumptions", "codes_and_standards", "methodology", "analysis", "results", "conclusions", "recommendations", "references", "appendices"]'::jsonb,
 '{"h1": "Heading 1", "h2": "Heading 2"}'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO document_templates (company_id, doc_type, section_order, heading_style) VALUES
('demo_company', 'calculation_narrative',
 '["title", "scope", "assumptions", "design_codes", "load_cases_and_combinations", "inputs_and_materials", "calculations", "results", "qa_checks", "attachments"]'::jsonb,
 '{"h1": "Heading 1", "h2": "Heading 2"}'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO document_templates (company_id, doc_type, section_order, heading_style) VALUES
('demo_company', 'method_statement',
 '["title", "scope", "responsibilities", "references", "materials_and_equipment", "methodology", "quality_assurance", "safety", "environmental", "hold_points"]'::jsonb,
 '{"h1": "Heading 1", "h2": "Heading 2"}'::jsonb)
ON CONFLICT DO NOTHING;
