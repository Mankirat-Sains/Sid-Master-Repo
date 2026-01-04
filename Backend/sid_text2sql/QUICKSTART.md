# Quick Start Guide

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-openai-api-key"
   $env:SUPABASE_DB_URL="postgresql://user:password@host:port/dbname"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-openai-api-key"
   export SUPABASE_DB_URL="postgresql://user:password@host:port/dbname"
   ```

   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   SUPABASE_DB_URL=postgresql://user:password@host:port/dbname
   ```

## Usage

### Option 1: Python Script

```python
from assistant import TextToSQLAssistant

assistant = TextToSQLAssistant(
    connection_string="postgresql://user:password@host:port/dbname"
)

result = assistant.query("Find all projects in Kitchener")
print(result["sql"])
print(result["results"])
```

### Option 2: REST API

1. **Start the server:**
   ```bash
   python api.py
   # or
   uvicorn api:app --reload
   ```

2. **Make a request:**
   ```bash
   curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Find all projects",
       "connection_string": "postgresql://user:password@host:port/dbname",
       "execute": true
     }'
   ```

## Example Queries

- "List all tables in the database"
- "Search for documents containing 'structural beam'"
- "Find projects with more than 100 chunks"
- "Find chunks similar to 'concrete design' in project PROJ001"
- "Show me all projects in Kitchener"
- "Count total number of document chunks"

## Troubleshooting

### Connection Errors
- Verify your connection string format: `postgresql://user:password@host:port/dbname`
- Check that your database is accessible
- Ensure credentials are correct

### OpenAI API Errors
- Verify your API key is set correctly
- Check your OpenAI account has credits
- Try a different model (gpt-3.5-turbo is cheaper)

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

