## Project Resolution Before Retrieval

Goal: let the assistant say a project exists (and open its Speckle model) even when no documents are indexed, instead of replying "not listed".

### How it works
- The resolver looks at:
  - `project_info` (Supabase) for project metadata (key, name, address, city, postal code, speckle IDs).
  - `alias_names` on `project_info` (Supabase) for aliases (used for fuzzy matching).
  - `Backend/references/speckle_mapping.json` for `projectId`/`modelId` (fallback; keep in sync with DB).
- It extracts candidate project keys/names from the user query (regex + quoted text).
- If a match is found, it returns a stub doc with metadata so the pipeline can respond "✅ Project exists" rather than "not listed".
- RAG retrieval still runs when data exists; otherwise the stub is returned.

### Files added/changed
- `Backend/database/project_resolver.py`
  - `resolve_project(name_or_key)`: queries `project_info`, `project_aliases`, and speckle mapping (fuzzy).
  - `extract_project_keys(text)`: pulls probable project keys/names from free text.
- `Backend/nodes/DBRetrieval/retrieve.py`
  - On no retrieval results, it now calls the resolver; if a project is found, it returns a minimal stub doc instead of an empty set.

### Data dependencies
- `project_info` should contain the primary project metadata (e.g., `project_key`, `project_name`, optionally `speckle_project_id`, `speckle_model_id`, `alias_names`). Fuzzy matching uses `project_name`, `project_key`, and `alias_names`.
- `Backend/references/speckle_mapping.json` is used as a fallback mapping (useful while DB is being populated).
- No changes to chunk ingestion required; this is a graceful fallback for "no docs yet" scenarios.

### What to expect
- If a project exists in `project_info` or speckle mapping but has zero indexed docs, the assistant can still acknowledge it and pass Speckle IDs to the viewer.
- Only when neither metadata nor mapping exists will it fall back to "not listed".
