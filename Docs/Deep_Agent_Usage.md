# Deep Agent Usage Guide

## Enabling the Deep Agent
```bash
# .env
DEEP_AGENT_ENABLED=true
```

## Quick Tests
### 1) Basic deep agent planning
```python
state = {
    "session_id": "test123",
    "user_query": "Create a document about AI safety",
    "workflow": "docgen",
    "task_type": "doc_report"
}
```

### 2) Interrupt flow (manual)
1) Send a request that triggers a destructive action (e.g., write/delete a file).  
2) Observe `type: "interrupt"` event from `/chat/stream` with `action_id`.  
3) POST to `/approve-action` with that `action_id` and `approved=true`.  
4) Verify graph resumes and completes.

### 3) Workspace inspection
```bash
ls /workspace/{session_id}
```

## API Endpoints
### Chat streaming with interrupts
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write test.txt with hello world",
    "session_id": "test123"
  }'
```

### Action approval
```bash
curl -X POST http://localhost:8000/approve-action \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "write_file_abc123",
    "approved": true,
    "reason": "Looks safe",
    "session_id": "test123"
  }'
```

## Troubleshooting
1) Workspace permissions: ensure `WORKSPACE_BASE_PATH` is writable.  
2) Interrupt not firing: confirm `INTERRUPT_DESTRUCTIVE_ACTIONS=true`.  
3) State compatibility: verify deep-agent fields exist (see `RAGState`/`ensure_rag_state_compatibility`).  
4) Missing traces: ensure `EXECUTION_TRACE_ENABLED` and check `execution_trace` in responses.  
5) Approval not sticking: confirm `desktop_approved_actions` is persisted in state and that the same `action_id` is reused.
