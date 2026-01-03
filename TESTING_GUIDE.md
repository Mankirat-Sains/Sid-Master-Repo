# Testing Guide for Backend_new

## Quick Start

### 1. Test Imports First
Before starting the server, verify all imports work:

```bash
cd Backend_new
python test_setup.py
```

This will check:
- ✅ Config imports
- ✅ Model imports  
- ✅ Database imports
- ✅ Node imports
- ✅ Graph builder
- ✅ Main entry point
- ✅ API server

### 2. Start the API Server

```bash
cd Backend_new
python api_server.py
```

The server will start on port 8000 (or PORT from .env) and show:
```
🚀 Starting Mantle RAG API Server...
   Chat endpoint: http://0.0.0.0:8000/chat
   Health check: http://0.0.0.0:8000/health
   Database status: http://0.0.0.0:8000/db/health
```

### 3. Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

Or open in browser: http://localhost:8000/health

#### Database Health
```bash
curl http://localhost:8000/db/health
```

#### Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What projects have retaining walls?",
    "session_id": "test"
  }'
```

### 4. Common Issues & Fixes

#### Import Errors
If you see import errors:
- Make sure you're in the `Backend_new` directory
- Check that all `__init__.py` files exist
- Verify `.env` file is in the parent directory or Backend_new

#### Missing Environment Variables
The system needs:
- `OPENAI_API_KEY` (required)
- `SUPABASE_URL` (required)
- `SUPABASE_ANON_KEY` (required)
- `ANTHROPIC_API_KEY` (optional, if using Claude models)

#### Vector Store Not Initialized
If `vs_smart` or `vs_large` are None:
- Check Supabase credentials in `.env`
- Verify database tables exist
- Check network connectivity

### 5. Debug Mode

To see detailed logs, check:
- Console output (all logs go to console)
- Enhanced logs: http://localhost:8000/logs/enhanced?format=html
- Log stats: http://localhost:8000/logs/enhanced/stats

### 6. Verify Reference Files

Check if reference files loaded correctly:
```bash
curl http://localhost:8000/debug/categories
```

Should show:
- `planner_playbook.md` loaded from `references/` folder
- `project_categories.md` loaded from `references/` folder

## File Structure Check

Make sure you have:
```
Backend_new/
├── api_server.py          ✅
├── main.py                ✅
├── config/                  ✅
├── models/                  ✅
├── database/                ✅
├── nodes/                   ✅
├── prompts/                 ✅
├── utils/                   ✅
├── synthesis/               ✅
├── graph/                   ✅
├── helpers/                 ✅
├── references/              ✅
│   ├── planner_playbook.md
│   └── project_categories.md
└── .env                     ✅ (in parent or here)
```

## Next Steps

Once everything works:
1. Test with your Electron app
2. Monitor logs for any issues
3. Adjust reference files in `references/` folder as needed

