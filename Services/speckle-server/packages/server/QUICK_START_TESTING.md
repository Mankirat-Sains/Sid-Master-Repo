# Quick Start: Testing AI Service Integration

## Step 1: Start the AI Service

Open a terminal and run:

```bash
cd packages/ai-service

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
API_KEY=test-api-key-123
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=*
EOF

# Start the service
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

## Step 2: Configure Server Environment

In your server environment (`.env` file or environment variables):

```bash
export AI_SERVICE_ORIGIN=http://localhost:8001
export AI_SERVICE_API_KEY=test-api-key-123
```

## Step 3: Start the Server

In another terminal:

```bash
cd packages/server
yarn dev
```

## Step 4: Run Tests

### Option A: Automated Test Script

```bash
# From packages/server directory
export AI_SERVICE_API_KEY=test-api-key-123
export AUTH_TOKEN=your-speckle-token  # Optional, for full proxy test

node test-ai-integration.js
```

### Option B: Manual curl Tests

**1. Test AI Service directly:**

```bash
# Health check
curl http://localhost:8001/health

# Should return: {"status":"ok","service":"ai-service"}
```

**2. Test AI Service with API key:**

```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"message": "Hello"}'

# Should return: {"response":"Mock response to: Hello","model":"mock"}
```

**3. Test Server Proxy (without auth - should fail):**

```bash
curl -X POST http://localhost:3000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Should return: 401 Unauthorized
```

**4. Test Server Proxy (with auth - should succeed):**

```bash
# Replace YOUR_TOKEN with a valid Speckle auth token
curl -X POST http://localhost:3000/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Hello"}'

# Should return: {"response":"Mock response to: Hello","model":"mock"}
```

## Expected Results

✅ **All tests passing means:**

- AI service is running and responding
- API key authentication works
- Server can proxy requests to AI service
- Authentication middleware is working
- Services can communicate

## Troubleshooting

**AI Service won't start:**

- Check Python version: `python --version` (needs 3.12+)
- Check port 8001 is available: `lsof -i :8001` (Linux/Mac) or `netstat -ano | findstr :8001` (Windows)

**Server can't connect to AI Service:**

- Verify AI service is running: `curl http://localhost:8001/health`
- Check `AI_SERVICE_ORIGIN` environment variable
- Verify `AI_SERVICE_API_KEY` matches in both services
- Check server logs for proxy errors

**Proxy returns 502 Bad Gateway:**

- AI service is not running or not reachable
- Check `AI_SERVICE_ORIGIN` is correct
- Verify API key matches: `AI_SERVICE_API_KEY` in server = `API_KEY` in AI service

**401 Unauthorized on proxy:**

- This is expected without auth token
- Get a valid auth token from your Speckle server
- Use `Authorization: Bearer <token>` header

