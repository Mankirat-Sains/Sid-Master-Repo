# Backend Setup Guide

## Which Backend to Use?

✅ **Use `/Frontend/backend/main.py`** - This is the FastAPI web server that the frontend connects to.

❌ **Don't use `/Frontend/agents/run_multi_agent.py`** - This is a CLI testing script, not a web server.

## Quick Start

### 1. Install Backend Dependencies

```bash
cd "/Volumes/J:/Sid-Master-Repo/Frontend/backend"
pip install -r requirements.txt
```

### 2. Create `.env` File

Create a `.env` file in `/Volumes/J:/Sid-Master-Repo/Frontend/` (parent directory of both `backend` and `Frontend` folders) with:

```env
# Required for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Required for database access
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
# OR use SUPABASE_KEY instead of SUPABASE_ANON_KEY
```

### 3. Start the Backend Server

```bash
cd "/Volumes/J:/Sid-Master-Repo/Frontend/backend"
python main.py
```

The server will start on `http://localhost:8000`

### 4. Verify Backend is Running

Open your browser and check:
- Health endpoint: http://localhost:8000/health
- Root endpoint: http://localhost:8000/

You should see JSON responses indicating the server is running.

## Frontend Connection

The frontend is already configured to connect to `http://localhost:8000` by default. 

If you need to change the backend URL, create a `.env` file in `/Volumes/J:/Sid-Master-Repo/Frontend/Frontend/` with:

```env
ORCHESTRATOR_URL=http://localhost:8000
# OR
RAG_API_URL=http://localhost:8000
```

## Architecture

```
Frontend (Nuxt.js on port 3000)
    ↓ HTTP POST /chat
Backend (FastAPI on port 8000)
    ↓ Uses
Agents System (/Frontend/agents/)
    ↓ Uses
- OpenAI API (for LLM)
- Supabase (for vector database)
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is already in use

### "Agents system not available"
- Make sure `/Frontend/agents/` directory exists
- Check that agents can be imported (Python path is correct)
- Verify `.env` file is in the correct location

### "AI not enabled"
- Set `OPENAI_API_KEY` in your `.env` file
- Restart the backend server after adding environment variables

### Frontend can't connect to backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings (backend already has CORS enabled for all origins)
- Verify frontend `.env` has correct `ORCHESTRATOR_URL`

## Endpoints

- `GET /` - Root endpoint (health check)
- `GET /health` - Detailed health status
- `POST /chat` - Main chat endpoint (used by frontend)
- `POST /export/word` - Word document export

## Next Steps

1. ✅ Start backend: `python main.py` in `/Frontend/backend/`
2. ✅ Start frontend: `npm run dev` in `/Frontend/Frontend/`
3. ✅ Open browser: http://localhost:3000
4. ✅ Test chat functionality!


