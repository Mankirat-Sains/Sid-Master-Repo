# Installation Guide

## Install Dependencies

You need to install the required Python packages. Run this command in your terminal:

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/GraphQL-MCP/fact_engine_service"
pip3 install -r requirements.txt
```

If you get permission errors, try:

```bash
pip3 install --user -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Required Packages

The service needs these packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `pydantic-settings` - Settings management
- `psycopg2-binary` - PostgreSQL driver (if using SQL)
- `asyncpg` - Async PostgreSQL driver (optional)
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable loading
- `httpx` - HTTP client for GraphQL

## Verify Installation

After installing, verify packages are available:

```bash
python3 -c "import fastapi; import openai; import psycopg2; print('✅ All packages installed')"
```

## Troubleshooting

**Permission Errors:**
- Use `--user` flag: `pip3 install --user -r requirements.txt`
- Or use a virtual environment (see above)

**Python Version:**
- Requires Python 3.8 or higher
- Check version: `python3 --version`

**Missing Packages:**
- If a specific package fails, install it individually:
  ```bash
  pip3 install fastapi uvicorn pydantic pydantic-settings openai python-dotenv httpx
  ```


