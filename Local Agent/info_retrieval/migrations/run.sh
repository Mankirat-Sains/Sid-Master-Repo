#!/usr/bin/env bash
set -euo pipefail

# Simple migration runner for Supabase/Postgres migrations in this folder.
# Usage: SUPABASE_DB_URL="postgres://..." ./run.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_URL="${SUPABASE_DB_URL:-}"

if [ -z "$DB_URL" ]; then
  echo "SUPABASE_DB_URL is required (postgres://...)" >&2
  exit 1
fi

migrations=(
  "001_create_document_templates.sql"
  "002_create_section_templates.sql"
  "003_create_style_rules.sql"
  "004_template_sections.sql"
)

for mig in "${migrations[@]}"; do
  path="${ROOT_DIR}/${mig}"
  echo "🔄 Applying migration: ${mig}"
  psql "$DB_URL" -f "$path"
done

echo "✅ Migrations complete"
