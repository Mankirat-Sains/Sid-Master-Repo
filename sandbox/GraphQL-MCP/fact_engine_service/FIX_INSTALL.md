# Quick Fix: Install Dependencies

You're getting `ModuleNotFoundError: No module named 'asyncpg'` because dependencies aren't installed.

## Quick Fix

Run this command in your terminal:

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/GraphQL-MCP/fact_engine_service"
pip3 install -r requirements.txt
```

## If You Get Permission Errors

Try with `--user` flag:

```bash
pip3 install --user -r requirements.txt
```

## Or Use Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Now run the service
python main.py
```

## Minimal Installation (GraphQL Only)

If you're only using GraphQL (not PostgreSQL), you can install just the essentials:

```bash
pip3 install fastapi uvicorn pydantic pydantic-settings openai python-dotenv httpx
```

The `asyncpg` and `psycopg2-binary` packages are only needed if you're using PostgreSQL database connections.

## After Installation

Once installed, try running again:

```bash
python3 main.py
```

You should see:
```
✅ Semantic planner initialized
✅ Fact executor initialized (GraphQL: True)
✅ Answer composer initialized
```


