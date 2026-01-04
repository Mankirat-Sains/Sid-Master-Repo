# Schema Parsing Fix - The Real Problem

## The Issue

**Problem**: The LLM was getting a 126,333 character schema but only seeing the first 1000 characters, so it couldn't understand what queries were actually available.

**Result**: 
- LLM tried `{ projects { name id } }` → Error: "Cannot query field 'projects'"
- LLM tried `{ project { name id } }` → Error: "Field 'project' requires 'id' argument"

## Root Cause

**Location**: `test_natural_language.py` line 173
```python
result = {"schema": schema[:1000] + "..." if len(schema) > 1000 else schema}
```

The schema was being truncated to 1000 chars, so the LLM never saw:
- The actual Query type definition
- What queries are available
- What arguments they need
- Example query structures

## The Fix

**Created**: `schema_parser.py`
- Parses the full GraphQL schema (JSON introspection or SDL)
- Extracts just the Query type fields
- Generates example queries
- Formats a clean summary for the LLM

**Updated**: `test_natural_language.py`
- Now parses schema and sends structured summary to LLM
- Includes:
  - List of available queries
  - Query signatures with arguments
  - Example queries the LLM can use

## What the LLM Now Sees

Instead of:
```
"schema": "type Query { ... (truncated at 1000 chars)"
```

The LLM now gets:
```json
{
  "schema_summary": "# GraphQL Schema Summary\n## Available Queries:\n### projects\n  Returns: [Project!]!\n### project\n  Arguments:\n    - id: String (required)\n  Returns: Project\n## Example Queries:\n```graphql\n{ projects { id name } }\n```",
  "available_queries": ["projects", "project", "streams", "stream", ...],
  "example_queries": ["{ projects { id name } }", "{ project(id: \"ID_VALUE\") { id name } }"]
}
```

## How It Works Now

1. **LLM calls introspect-schema**
2. **Schema parser extracts Query type** → Finds all available queries
3. **Generates examples** → Shows LLM how to structure queries
4. **LLM sees clean summary** → Knows exactly what queries exist
5. **LLM constructs correct query** → Uses the right query name and structure

## Testing

Run the test again:
```bash
python3 test_natural_language.py "What projects are available in Speckle?"
```

**Expected behavior**:
- LLM sees "projects" in available_queries list
- LLM uses example query: `{ projects { id name } }`
- Query executes successfully
- Returns actual project data

## If It Still Fails

If the query still fails, check:
1. **Does "projects" query exist?** - Look at available_queries in the output
2. **Does it require authentication?** - Check if you need to query "activeUser.projects" instead
3. **Are there errors in the response?** - The error message will tell you what's wrong

The schema parser will show you exactly what queries are available, so you can debug more easily.


