-- Migration: 002_create_section_templates.sql

CREATE TABLE IF NOT EXISTS section_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    section_type TEXT NOT NULL,

    -- Template definition
    skeleton TEXT NOT NULL,        -- Scaffold prompt with placeholders
    required_elements JSONB,       -- {"codes": true, "assumptions": true, ...}
    example_length TEXT,           -- 'short' | 'medium' | 'long'

    -- Metadata
    schema_version TEXT NOT NULL DEFAULT '1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_company_doc_section UNIQUE(company_id, doc_type, section_type)
);

CREATE INDEX IF NOT EXISTS idx_section_templates_company ON section_templates(company_id);
CREATE INDEX IF NOT EXISTS idx_section_templates_lookup ON section_templates(company_id, doc_type, section_type);

-- Seed data for demo
INSERT INTO section_templates (company_id, doc_type, section_type, skeleton, required_elements) VALUES
('demo_company', 'design_report', 'methodology',
 E'This section describes the analytical approach and methods used for the design.\n\nStructure:\n1. Objective and scope of the analysis\n2. Software/tools and versions used (e.g., ETABS v20, SAP2000 v24)\n3. Governing codes/standards and project-specific criteria\n4. Load cases and combinations considered\n5. Key assumptions and simplifications\n6. Calculation methodology (step-by-step)\n7. Quality checks / verification steps\n\nTone: Technical, formal, past tense for completed work. Cite codes explicitly.',
 '{"codes": true, "software": true, "assumptions": true, "load_combinations": true, "qa_checks": true}'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO section_templates (company_id, doc_type, section_type, skeleton, required_elements) VALUES
('demo_company', 'design_report', 'assumptions',
 E'Document all assumptions made in the analysis.\n\nFormat:\n- Numbered list of assumptions\n- For each: statement, basis (code / standard practice / engineering judgment), conservatism notes\n- Identify any deviations from typical practice\n- Note any required confirmations (e.g., site data, supplier data)\n\nTone: Precise, factual, defensive (justify choices).',
 '{"codes": false, "justification": true, "conservatism": true, "deviations": true}'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO section_templates (company_id, doc_type, section_type, skeleton, required_elements) VALUES
('demo_company', 'calculation_narrative', 'methodology',
 E'Describe the calculation procedure step-by-step.\n\nRequired:\n- Reference design codes (ACI, AISC, ASCE, etc.) and project criteria\n- List load cases and combinations used\n- Describe analysis method (hand calc, spreadsheet, FEA) with key equations or references\n- Note any software used and version\n- Identify checks/verification steps and acceptance criteria\n\nTone: Methodical, precise, third-person.',
 '{"codes": true, "load_combinations": true, "software": true, "qa_checks": true}'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO section_templates (company_id, doc_type, section_type, skeleton, required_elements) VALUES
('demo_company', 'design_report', 'results',
 E'Present key results, governing criteria, and compliance.\n\nStructure:\n1. Summary of results (pass/fail, governing case)\n2. Tabulated key values (loads, stresses, deflections) with units\n3. Code/standard clauses referenced for acceptance\n4. Notes on limitations or follow-up actions\n\nTone: Concise, evidence-based, cite sources.',
 '{"codes": true, "tables": true, "follow_up": true}'::jsonb)
ON CONFLICT DO NOTHING;
