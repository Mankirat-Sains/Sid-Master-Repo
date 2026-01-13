# Interrupt Handling Guide

## How Interrupts Work
### 1) Detection
- Destructive desktop actions (write_file, edit_file, delete_file, materialize_doc) trigger interrupts when `INTERRUPT_DESTRUCTIVE_ACTIONS=true`.

### 2) Propagation
- Deep loop raises `GraphInterrupt`.
- API layer catches and returns a structured `interrupt` SSE event.
- State is saved with `desktop_interrupt_pending` and `desktop_interrupt_data`.

### 3) Approval Flow
1. Client receives interrupt details (includes `action_id`, `action`, context).  
2. User approves or rejects.  
3. Client calls `/approve-action` with decision.  
4. Graph resumes with updated state; further interrupts can occur.

## API Integration
### Streaming response format (excerpt)
```json
{
  "type": "interrupt",
  "interrupt": {
    "action_id": "write_file_abc123",
    "action": "write_file",
    "timestamp": "2025-01-01T00:00:00Z",
    "state_summary": {
      "workspace_dir": "/workspace/test123"
    }
  },
  "session_id": "test123"
}
```

### Approval request format
```json
{
  "action_id": "write_file_abc123",
  "approved": true,
  "reason": "File looks safe",
  "session_id": "test123"
}
```

## Testing Interrupts
### Manual test
```bash
# Trigger interrupt
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Delete important.txt", "session_id": "test1"}'

# Approve (use action_id from interrupt payload)
curl -X POST http://localhost:8000/approve-action \
  -H "Content-Type: application/json" \
  -d '{"action_id": "delete_file_xyz789", "approved": true, "session_id": "test1"}'
```

### Automated test sketch
1) Invoke `/chat/stream` with a destructive request; capture `action_id`.  
2) POST to `/approve-action` with `approved=true`.  
3) Verify resumed graph completes without another interrupt for the same action.  
4) Assert `desktop_approved_actions` contains the approved `action_id`.
