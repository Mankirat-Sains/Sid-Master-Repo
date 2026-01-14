# DOCX Service Agent - Integration Guide

This mirrors the Paul Excel agent but for DOCX edits. It exposes deterministic operations (insert/replace/delete/style/reorder) and returns structured change summaries so the backend/deep agent can show diffs and avoid blind rewrites.

## Architecture
```
Frontend (Nuxt)
    ↓ HTTP calls
Main Backend (api_server.py, /api/doc/* proxies)
    ↓
Doc Agent Service (doc_agent_api.py, port 8002)
    ↓
Workspace DOCX files (local disk)
```

## Setup
```bash
cd sandbox/doc-agent/Doc_Service_Agent
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.json config.json   # edit paths
python doc_agent_api.py --config config.json --port 8002
```

Example `config.json`:
```json
{
  "workspace_dir": "./workspace/doc-agent",
  "docs": [
    {
      "doc_id": "spec",
      "file_path": "./sample_docs/spec.docx"
    }
  ]
}
```

## API endpoints (service)
- `GET /health` — service status
- `POST /api/doc/configure` — load config at runtime
- `POST /api/doc/open` — `{file_path, doc_id?}` → doc structure (paragraphs/headings)
- `POST /api/doc/apply` — `{doc_id?, file_path?, ops[], save_as?}` → updated structure + change_summary
- `POST /api/doc/export` — `{doc_id, target_path?}` → saved copy metadata
- `GET /api/doc/history?doc_id=...` — recent ops

### Ops schema (minimum viable)
```json
{
  "ops": [
    {"op": "replace_text", "target": {"index": 3}, "text": "New text"},
    {"op": "insert_heading", "target": {"index": 5}, "level": 2, "text": "Schedule"},
    {"op": "insert_paragraph", "target": {"index": 6}, "text": "Bullet item", "style": "List Bullet"},
    {"op": "delete_block", "target": {"index": 8}},
    {"op": "set_style", "target": {"index": 2}, "style": "Heading 3"},
    {"op": "reorder_blocks", "from_index": 10, "to_index": 4}
  ]
}
```

Notes:
- `target.index` is a zero-based paragraph index.
- Insert operations place content **after** the referenced index (or append if at end).
- `save_as` can route output to a new file; otherwise edits apply in-place.

## Backend proxy (mirror the Excel agent pattern)
- Add `DOC_API_URL` env (default `http://localhost:8002`).
- Expose `/api/doc/*` endpoints that forward to the service:
  - `/api/doc/health`
  - `/api/doc/open`
  - `/api/doc/apply`
  - `/api/doc/export`
  - `/api/doc/history`
- On failure, return 502-style error with a friendly message (“Doc agent unreachable”).

## Frontend composable
- Create `useDocAgent.ts` mirroring `useSyncAgent.ts`:
  - `openDoc(filePath, docId?)`
  - `applyOps(docIdOrPath, ops, saveAs?)`
  - `exportDoc(docId, targetPath?)`
  - `getHistory(docId, limit?)`
  - optional `health()`
- All calls go through `orchestratorUrl` to `/api/doc/*`.

## Deep agent tool
- New tool `edit_document` calls `/api/doc/apply` with ops[] and returns `change_summary` + updated structure.
- Include doc_id/file_path in params so the tool can target workspace files created by docgen or user uploads.
- Surface errors as interrupt-friendly messages if destructive/ambiguous.

## Testing ideas
- Unit: `DocAgent.apply_ops` on a temp doc, asserting change_summary and paragraph order.
- API: FastAPI TestClient calling `/api/doc/apply` with a fixture doc.
- Proxy: backend `/api/doc/health` returns 200 with mocked doc agent URL.

## Operational tips
- Keep doc IDs stable (e.g., session-id + filename) so history is traceable.
- Store ops in history to enable replay/undo in the future.
- Gate destructive ops via deep agent interrupts if you expose “delete_block” from chat.
