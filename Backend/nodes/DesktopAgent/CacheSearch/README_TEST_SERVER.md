# CacheSearch Test Server

Standalone server for testing CacheSearch without the main API server.

## Start the Server

```bash
cd "/Volumes/J/Sid-Master-Repo/Backend/nodes/DesktopAgent/CacheSearch"
python test_server.py
```

Server runs on: **http://localhost:8002**

## Endpoints

### POST /chat
Main chat endpoint for testing.

**Request:**
```json
{
  "message": "[Context: User is working in project folder: /path/to/folder]\n\nTell me the info in this project",
  "session_id": "test"
}
```

**Response:**
```json
{
  "reply": "Answer from cache...",
  "citations": [...],
  "session_id": "test"
}
```

### GET /health
Health check endpoint.

### GET /test/folder?query=...
Test folder path extraction.

### GET /test/cache/{project_id}?query=...
Test cache search directly.

## Update Frontend to Use Test Server

Temporarily update `ProjectChat.vue` to use the test server:

```typescript
// In ProjectChat.vue, change the useChat import or create a test version
const response = await fetch('http://localhost:8002/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: contextMessage,
    session_id: sessionId
  })
})
const result = await response.json()
```

## Testing

1. Start test server: `python test_server.py`
2. Make sure cache exists for your test folder
3. Send a request with folder context
4. Check logs for CacheSearch activity
