# Quick Test Guide - Verify AI Service Integration

## Step-by-Step Testing

### Step 1: Start the AI Service

Open **Terminal 1** and run:

```bash
cd packages/ai-service

# Activate virtual environment (if not already active)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Start the service
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
INFO:     Started reloader process
```

### Step 2: Verify AI Service is Running

In **Terminal 1** (or a new terminal), test the health endpoint:

```bash
# Windows PowerShell:
curl http://localhost:8001/health

# Windows CMD:
curl http://localhost:8001/health

# Linux/Mac:
curl http://localhost:8001/health
```

**Expected response:**

```json
{ "status": "ok", "service": "ai-service" }
```

### Step 3: Test AI Service Directly (with API key)

```bash
# Windows PowerShell:
curl -X POST http://localhost:8001/api/v1/chat `
  -H "Content-Type: application/json" `
  -H "X-API-Key: test-api-key-123" `
  -d '{\"message\": \"Hello\"}'

# Windows CMD:
curl -X POST http://localhost:8001/api/v1/chat -H "Content-Type: application/json" -H "X-API-Key: test-api-key-123" -d "{\"message\": \"Hello\"}"

# Linux/Mac:
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"message": "Hello"}'
```

**Expected response:**

```json
{ "response": "Mock response to: Hello", "model": "mock" }
```

**If you get 401:** Your API key in `packages/ai-service/.env` doesn't match. Check the value.

### Step 4: Start the Server

Open **Terminal 2** and run:

```bash
cd packages/server

# Make sure your .env file has:
# AI_SERVICE_ORIGIN=http://localhost:8001
# AI_SERVICE_API_KEY=test-api-key-123

# Start the server
yarn dev
```

**Expected output:**

```
🚀 My name is Speckle Server, and I'm running at 127.0.0.1:3000
Initializing AI service module...
AI service module initialized
```

### Step 5: Test Server Proxy (without auth - should fail)

```bash
curl -X POST http://localhost:3000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**Expected response:** `401 Unauthorized` or `403 Forbidden`

This is correct - it means authentication is working!

### Step 6: Test Server Proxy (with auth token)

You'll need a valid Speckle auth token. Get one by:

1. Logging into your Speckle server
2. Going to your profile → Access Tokens
3. Creating a new token

Then test:

```bash
# Replace YOUR_TOKEN with your actual token
curl -X POST http://localhost:3000/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Hello from server proxy"}'
```

**Expected response:**

```json
{ "response": "Mock response to: Hello from server proxy", "model": "mock" }
```

## Quick Automated Test

Or use the automated test script:

```bash
cd packages/server

# Set environment variables
# Windows PowerShell:
$env:AI_SERVICE_API_KEY="test-api-key-123"
$env:AUTH_TOKEN="your-token-here"  # Optional

# Windows CMD:
set AI_SERVICE_API_KEY=test-api-key-123
set AUTH_TOKEN=your-token-here

# Linux/Mac:
export AI_SERVICE_API_KEY=test-api-key-123
export AUTH_TOKEN=your-token-here

# Run test
node test-ai-integration.js
```

## Success Checklist

- ✅ AI service starts on port 8001
- ✅ Health endpoint returns `{"status":"ok"}`
- ✅ AI service chat endpoint works with API key
- ✅ Server starts successfully
- ✅ Server proxy rejects requests without auth (401)
- ✅ Server proxy works with valid auth token

## Common Issues

**AI Service won't start:**

- Check Python is installed: `python --version`
- Check port 8001 is free: `netstat -ano | findstr :8001` (Windows) or `lsof -i :8001` (Linux/Mac)
- Verify `.env` file exists in `packages/ai-service/`

**Server can't connect to AI Service:**

- Check AI service is running: `curl http://localhost:8001/health`
- Verify `AI_SERVICE_ORIGIN=http://localhost:8001` in server `.env`
- Verify `AI_SERVICE_API_KEY` matches `API_KEY` in AI service `.env`
- Restart server after changing `.env`

**502 Bad Gateway:**

- AI service is not running
- `AI_SERVICE_ORIGIN` is incorrect
- API keys don't match

**401 Unauthorized on proxy:**

- This is expected without a token!
- Need a valid Speckle auth token for authenticated requests

## Next Steps

Once basic testing works:

1. ✅ Services can communicate
2. ✅ Authentication is working
3. ✅ Ready to add more features!

You can now proceed with your additional prompts to enhance the AI service functionality.

