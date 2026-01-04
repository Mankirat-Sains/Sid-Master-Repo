# Architecture Overview

This document explains how this text-to-SQL system is structured and how it compares to Supabase's AI assistant.

## System Architecture

The system follows a similar architecture to Supabase's AI assistant:

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Endpoint  │  (api.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Assistant     │  (assistant.py)
│  - Prompts      │
│  - Tool Calls   │
│  - LLM          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Tools       │  (tools.py)
│  - Schema Info  │
│  - SQL Execute  │
│  - Functions    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   Database      │
└─────────────────┘
```

## Component Comparison

### 1. Prompts (`prompts.py`)

**Supabase**: `lib/ai/prompts.ts`
- `GENERAL_PROMPT`: Role definition
- `CHAT_PROMPT`: Response style guidelines
- `PG_BEST_PRACTICES`: PostgreSQL best practices
- `RLS_PROMPT`: Row-level security guidance
- `EDGE_FUNCTION_PROMPT`: Edge function guidelines
- `REALTIME_PROMPT`: Realtime features

**Our System**: `prompts.py`
- `GENERAL_PROMPT`: Role definition (adapted)
- `CHAT_PROMPT`: Response style guidelines (adapted)
- `PG_BEST_PRACTICES`: PostgreSQL best practices (customized for knowledge graphs)
- `SCHEMA_CONTEXT_PROMPT`: Schema-specific context (NEW - tailored to your schema)
- `SECURITY_PROMPT`: Security guidelines (adapted)

**Key Differences**:
- Removed RLS, Edge Functions, and Realtime prompts (not relevant)
- Added schema-specific context for knowledge graphs, vector search, and document chunks
- Customized best practices for your specific schema patterns

### 2. Tools (`tools.py`)

**Supabase**: Multiple tool files
- `rendering-tools.ts`: UI tools (execute_sql, deploy_edge_function)
- `fallback-tools.ts`: Schema tools for self-hosted (getSchemaTables, getRlsKnowledge)
- `schema-tools.ts`: RLS policy tools (list_policies)
- `mcp-tools.ts`: Platform tools (list_tables, list_extensions, search_docs)

**Our System**: `tools.py` (consolidated)
- `list_tables`: List all tables
- `get_schema_info`: Get detailed schema information
- `list_functions`: List database functions (especially vector search)
- `get_table_comments`: Get table/column comments
- `execute_sql`: Execute SQL queries
- `get_indexes`: Get index information

**Key Differences**:
- Consolidated into single file (simpler for Python)
- Removed platform-specific tools (MCP, edge functions)
- Added schema-specific tools (functions, comments, indexes)
- Focused on read-only operations (no deployment tools)

### 3. Assistant (`assistant.py`)

**Supabase**: `lib/ai/generate-assistant-response.ts`
- Uses Vercel AI SDK
- Combines prompts dynamically
- Handles tool calls
- Streams responses
- Filters tools by opt-in level

**Our System**: `assistant.py`
- Uses OpenAI SDK directly
- Combines prompts statically
- Handles tool calls
- Returns complete responses
- No opt-in filtering (simpler)

**Key Differences**:
- Python instead of TypeScript
- OpenAI instead of multiple providers
- Simpler tool filtering (no opt-in levels)
- No streaming (can be added)

### 4. API Endpoint (`api.py`)

**Supabase**: `pages/api/ai/sql/generate-v4.ts`
- Next.js API route
- Handles authentication
- Validates messages
- Gets org AI details
- Streams responses

**Our System**: `api.py`
- FastAPI endpoint
- No authentication (add if needed)
- Validates requests with Pydantic
- No org management
- Returns JSON responses

**Key Differences**:
- FastAPI instead of Next.js
- Simpler (no auth, orgs, streaming)
- Can be extended with auth/streaming

## Schema-Specific Adaptations

### Vector Search Support
- Understands `match_documents()` function
- Knows about `smart_chunks` and `page_chunks` tables
- Supports `keyword_search_chunks()` function
- Handles embedding dimensions (1536 for text, 1024 for images)

### Document Management
- Understands chunk structure (project_key, page_id, chunk_index)
- Knows about metadata fields (title, summary, section_type)
- Supports project filtering

## Tool Execution Flow

1. **User Query**: "Find all projects in Kitchener"

2. **Assistant**:
   - Analyzes query
   - Determines need for schema info
   - Calls `get_schema_info()` tool

3. **Tool Execution**:
   - Queries database for schema
   - Returns table/column information

4. **Assistant** (with schema context):
   - Generates SQL using schema info
   - Calls `execute_sql()` tool

5. **Tool Execution**:
   - Executes SQL query
   - Returns results

6. **Response**:
   - Returns SQL, results, and explanation

## Extensibility

### Adding New Tools

1. Add tool function to `tools.py`:
```python
@tool("new_tool", "Description")
def new_tool(self, param: str) -> Dict[str, Any]:
    # Implementation
    return {"result": "..."}
```

2. Add to `_get_openai_tools()` in `assistant.py`:
```python
"new_tool": "Description of what it does"
```

3. Add parameters to `_get_tool_parameters()`:
```python
"new_tool": {
    "param": {
        "type": "string",
        "description": "..."
    }
}
```

### Adding New Prompts

1. Add prompt constant to `prompts.py`:
```python
NEW_PROMPT = """
# New Prompt Content
...
"""
```

2. Add to `_build_system_prompt()` in `assistant.py`:
```python
{NEW_PROMPT}
```

## Performance Considerations

- **Schema Caching**: Schema info is fetched on each query (could be cached)
- **Tool Calls**: Multiple tool calls add latency (could batch)
- **Query Limits**: No automatic limits (should add for safety)
- **Connection Pooling**: New connection per query (could pool)

## Security Considerations

- **SQL Injection**: Uses parameterized queries in tools
- **Destructive Operations**: Checks for DROP/TRUNCATE/DELETE
- **Connection Strings**: Passed in requests (should use auth)
- **API Keys**: Stored in environment (good practice)

## Future Enhancements

1. **Streaming**: Add streaming responses like Supabase
2. **Caching**: Cache schema info and common queries
3. **Auth**: Add authentication/authorization
4. **Multi-turn**: Support conversation history
5. **Query History**: Store and learn from queries
6. **Error Recovery**: Better error handling and retries
7. **Multiple Providers**: Support Anthropic, local models
8. **Connection Pooling**: Reuse database connections

