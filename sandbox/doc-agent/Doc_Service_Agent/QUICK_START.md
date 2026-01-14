# Quick Start - DOCX Service Agent

## What this is
A standalone FastAPI service that performs deterministic DOCX edits (insert/replace/delete/style/reorder). It mirrors the Paul Excel agent pattern so the backend and deep desktop agent can call structured document mutations.

## Fast path
```bash
cd sandbox/doc-agent/Doc_Service_Agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python doc_agent_api.py --config config.example.json --port 8002
```

### Sample calls (once running)
```bash
curl http://localhost:8002/health

# Open a doc (use absolute path or workspace-relative)
curl -X POST http://localhost:8002/api/doc/open \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/absolute/path/to/sample_docs/spec.docx"}'

# Apply edits
curl -X POST http://localhost:8002/api/doc/apply \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/absolute/path/to/sample_docs/spec.docx",
    "schema_version": 1,
    "ops": [
      {"op": "replace_text", "target": {"index": 1}, "text": "Updated intro"},
      {"op": "insert_heading", "target": {"index": 2}, "level": 2, "text": "Schedule"}
    ]
  }'

# Export (optional copy)
curl -X POST http://localhost:8002/api/doc/export \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "spec", "target_path": "./workspace/doc-agent/spec-out.docx"}'
```

## File structure
```
sandbox/doc-agent/Doc_Service_Agent/
├── doc_agent_api.py      # FastAPI service (port 8002 by default)
├── local_doc_agent.py    # DOCX editing engine (python-docx)
├── requirements.txt      # FastAPI + python-docx deps
├── config.example.json   # Example config (workspace + docs list)
└── sample_docs/          # Put sample .docx files here
```

## Environment
- `DOC_API_URL` in the main backend to point proxies to the service (default `http://localhost:8002`).
- Workspace defaults to `./workspace/doc-agent` (created automatically).

## Next steps
1) Wire backend proxy `/api/doc/*` to `DOC_API_URL` (mirrors Excel agent proxy).  
2) Add frontend composable `useDocAgent.ts` for open/apply/export/history.  
3) Add deep desktop tool wrapper that calls `/api/doc/apply` with ops[].  
