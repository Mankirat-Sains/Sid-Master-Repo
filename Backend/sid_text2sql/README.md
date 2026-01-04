# Text-to-SQL System

A text-to-SQL system inspired by Supabase's AI assistant, tailored for your specific Supabase schema. This system converts natural language questions into SQL queries using OpenAI's GPT models and provides tools for schema exploration and query execution.

## Features

- **Natural Language to SQL**: Convert questions into SQL queries using GPT-4
- **Schema-Aware**: Automatically understands your database schema (chunks, projects, embeddings, etc.)
- **Tool-Based Architecture**: Uses tools for schema exploration before generating SQL
- **Vector Search Support**: Understands vector similarity search functions (`match_documents`, `keyword_search_chunks`, etc.)
- **Safe Execution**: Validates queries and prevents destructive operations without confirmation

## Architecture

The system is based on Supabase's AI assistant architecture:

1. **Prompts** (`prompts.py`): System prompts that guide the AI, tailored to your schema
2. **Tools** (`tools.py`): Database tools for schema exploration and SQL execution
3. **Assistant** (`assistant.py`): Main assistant class that combines prompts and tools
4. **API** (`api.py`): FastAPI endpoint for serving requests

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export SUPABASE_DB_URL="postgresql://user:password@host:port/dbname"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
SUPABASE_DB_URL=postgresql://user:password@host:port/dbname
```

## Usage

### Python API

```python
from assistant import TextToSQLAssistant

# Initialize assistant
assistant = TextToSQLAssistant(
    connection_string="postgresql://user:password@host:port/dbname",
    model="gpt-4o"
)

# Query the database
result = assistant.query("Find all projects in Kitchener")

print(result["sql"])
print(result["results"])
print(result["explanation"])
```

### REST API

Start the server:
```bash
python api.py
# or
uvicorn api:app --host 0.0.0.0 --port 8000
```

Query endpoint:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find all projects with more than 100 document chunks",
    "connection_string": "postgresql://user:password@host:port/dbname",
    "execute": true
  }'
```

Generate SQL only (without execution):
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find all projects with more than 100 document chunks",
    "connection_string": "postgresql://user:password@host:port/dbname"
  }'
```

Get schema information:
```bash
curl "http://localhost:8000/schema?connection_string=postgresql://user:password@host:port/dbname"
```

## Available Tools

The assistant has access to these tools:

- `list_tables`: List all tables in the database
- `get_schema_info`: Get detailed schema information (columns, types, constraints)
- `list_functions`: List database functions (especially vector search functions)
- `get_table_comments`: Get table and column comments
- `execute_sql`: Execute SQL queries
- `get_indexes`: Get index information for performance analysis

## Schema-Specific Features

This system is tailored to your schema which includes:

- **Document Chunks**: `smart_chunks` and `page_chunks` with vector embeddings
- **Vector Search**: Functions like `match_documents()`, `keyword_search_chunks()`
- **Project Management**: `project_info` and `project_description` tables
- **Image Analysis**: `image_embeddings` and `image_descriptions` tables

## Example Queries

### Document Search
- "Find documents similar to 'structural beam design'"
- "Search for 'concrete strength' in project documents"
- "Find chunks about 'foundation design' in specific projects"

### Project Queries
- "List all projects with their descriptions"
- "Find projects with more than 100 chunks"
- "Get project information for project_key 'PROJ001'"

### Vector Search
- "Find documents similar to this embedding vector"
- "Search for images similar to a given image embedding"

## Configuration

### Models

Default model is `gpt-4o`. You can use:
- `gpt-4o` (recommended, best performance)
- `gpt-4-turbo-preview`
- `gpt-3.5-turbo` (faster, less accurate)

### Connection String Format

```
postgresql://[user[:password]@][host][:port][/dbname][?param1=value1&...]
```

Example:
```
postgresql://postgres:password@localhost:5432/mydb
```

## Error Handling

The system handles:
- Invalid SQL generation
- Database connection errors
- Tool execution errors
- Destructive operation prevention

## Security

- Destructive operations (DROP, TRUNCATE, DELETE without WHERE) require explicit confirmation
- SQL injection prevention through parameterized queries
- Connection string validation

## Development

### Project Structure

```
sid_text2sql/
├── prompts.py          # System prompts
├── tools.py            # Database tools
├── assistant.py        # Main assistant class
├── api.py              # FastAPI endpoint
├── requirements.txt    # Dependencies
├── README.md          # This file
└── schema.sql         # Database schema
```

### Testing

Test the assistant:
```python
from assistant import TextToSQLAssistant

assistant = TextToSQLAssistant(connection_string="...")
result = assistant.query("Your test question here")
print(result)
```

## Limitations

- Requires OpenAI API key (paid service)
- Database connection must be accessible from the server
- Large result sets may be slow
- Complex queries may require multiple tool calls

## Future Enhancements

- Support for other LLM providers (Anthropic, local models)
- Query caching
- Query history and learning
- Better error recovery
- Streaming responses
- Multi-turn conversations

## License

MIT License

## Acknowledgments

Inspired by Supabase's AI assistant architecture. See the Supabase repository for the original implementation.

