-- Migration: 003_create_style_rules.sql

CREATE TABLE IF NOT EXISTS style_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    rule_type TEXT NOT NULL,  -- 'tone' | 'format' | 'wording' | 'structure'

    -- Rules definition
    rules TEXT NOT NULL,      -- Plain English instructions for LLM
    banned_phrases JSONB,
    preferred_phrases JSONB,

    -- Metadata
    priority INTEGER DEFAULT 0,  -- Higher = more important
    schema_version TEXT NOT NULL DEFAULT '1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_style_rules_company ON style_rules(company_id);
CREATE INDEX IF NOT EXISTS idx_style_rules_type ON style_rules(company_id, rule_type);

-- Seed data for demo
INSERT INTO style_rules (company_id, rule_type, rules, banned_phrases, preferred_phrases, priority) VALUES
('demo_company', 'tone',
 'Use formal engineering register. Third person or passive voice. Past tense for completed work; present tense for facts. Be precise and definitive. Avoid hedging.',
 '["we think", "we believe", "maybe", "might", "probably", "seems like", "could be", "appears to"]'::jsonb,
 '["the analysis demonstrates", "results indicate", "per", "in accordance with", "consistent with"]'::jsonb,
 10)
ON CONFLICT DO NOTHING;

INSERT INTO style_rules (company_id, rule_type, rules, banned_phrases, preferred_phrases, priority) VALUES
('demo_company', 'wording',
 'Use standard engineering terminology. Reference codes/standards by official designation (e.g., "ACI 318-19"). Spell out acronyms on first use. Use SI units unless client specifies Imperial. Cite equations and tables by number when available.',
 '["utilize", "at this point in time", "kind of", "sort of"]'::jsonb,
 '["in accordance with", "as per", "per", "reference", "specified in", "per Clause", "per Table"]'::jsonb,
 5)
ON CONFLICT DO NOTHING;

INSERT INTO style_rules (company_id, rule_type, rules, banned_phrases, preferred_phrases, priority) VALUES
('demo_company', 'format',
 'Start sections with a 1-2 sentence overview. Use numbered lists for procedures/steps. Use bullets for assumptions/findings. Include code references in parentheses. Cross-reference figures/tables explicitly (e.g., "see Table 2", "refer to Figure 3"). Keep sentences concise.',
 NULL,
 '["see Table", "refer to Figure", "per Table", "per Figure"]'::jsonb,
 3)
ON CONFLICT DO NOTHING;

INSERT INTO style_rules (company_id, rule_type, rules, banned_phrases, preferred_phrases, priority) VALUES
('demo_company', 'structure',
 'Follow the provided section templates. Do not add new sections. Preserve section order and required elements. Keep headings consistent with template titles.',
 NULL,
 NULL,
 2)
ON CONFLICT DO NOTHING;
