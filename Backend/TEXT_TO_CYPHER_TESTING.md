# Text-to-Cypher Endpoint Testing Guide

## Overview

This guide explains how to test the Text-to-Cypher integration, which converts natural language queries to Cypher queries and executes them against the KuzuDB graph database.

## Prerequisites

### 1. Environment Setup

Ensure `DEBUG_MODE=True` in your `.env` file:

```bash
DEBUG_MODE=True
```

### 2. Start the Backend Server

```bash
cd /home/proffessorq/Work/Sid-Master-Repo/Backend
python api_server.py
```

You should see:

```
🚀 Starting Mantle RAG API Server...
   Chat endpoint: http://0.0.0.0:8000/chat
   Health check: http://0.0.0.0:8000/health
   🛠️  Kuzu Graph DB Schema: http://0.0.0.0:8000/graph/schema
   🔍 Natural Language → Cypher: http://0.0.0.0:8000/graph/query

📡 Server running on port: 8000
⚡ Ready for Electron chatbutton app!
```

### 3. Verify Database is Loaded

Check that KuzuDB has data:

```bash
curl http://localhost:8000/graph/schema | jq '.tables | length'
```

Expected: Should return a number > 0 (indicating tables exist)

## API Endpoint

### POST `/graph/query`

**Description**: Convert natural language to Cypher query and execute against KuzuDB.

**Request Body**:
```json
{
  "query": "How many projects are in the database?"
}
```

**Response**:
```json
{
  "success": true,
  "cypher_query": "MATCH (p:Project) RETURN count(p) AS project_count",
  "verification_result": {
    "approved": true,
    "safety_passed": true,
    "schema_passed": true,
    "syntax_passed": true,
    "kuzu_compatibility_passed": true,
    "issues": [],
    "warnings": []
  },
  "columns": ["project_count"],
  "rows": [[26]],
  "row_count": 1,
  "reasoning": "Simple count aggregation query for all Project nodes.",
  "confidence": 1.0,
  "latency_ms": 1234.5,
  "error": null
}
```

## Testing Methods

### Method 1: Automated Test Script (Recommended)

Run the comprehensive test suite:

```bash
cd /home/proffessorq/Work/Sid-Master-Repo/Backend
bash test_text_to_cypher_endpoint.sh
```

This script runs 7 test cases covering:
- Simple count queries
- List queries
- Structural queries (walls, beams)
- Project-specific queries
- Aggregation queries
- Invalid queries (should be rejected)
- Neo4j-specific syntax (should be rejected)

### Method 2: Manual curl Commands

#### Test 1: Simple Count Query

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many projects are in the database?"}'
```

**Expected Result**:
- `success`: true
- `cypher_query`: "MATCH (p:Project) RETURN count(p) AS project_count"
- `rows`: [[26]] (or your actual project count)

#### Test 2: List All Projects

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all projects with their names"}' | jq '.'
```

**Expected Result**:
- `success`: true
- `rows`: Array of project names
- `row_count`: Should match number of projects

#### Test 3: Structural Walls Query

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many structural walls are there?"}' | jq '.'
```

**Expected Result**:
- `success`: true
- Cypher query should filter by `w.structural = true`

#### Test 4: Project-Specific Query

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all walls in project 25-01-161"}' | jq '.'
```

**Expected Result**:
- `success`: true
- Cypher query should traverse: Project → Model → Version → Wall
- `rows`: Array of wall data from that project

#### Test 5: Aggregation Query

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Count beams by level"}' | jq '.'
```

**Expected Result**:
- `success`: true
- Cypher query should use `GROUP BY` pattern
- `rows`: Array of [level, count] pairs

#### Test 6: Invalid Query (Should Fail)

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Delete all projects"}' | jq '.'
```

**Expected Result**:
- `success`: false
- `verification_result.approved`: false
- `verification_result.issues`: Should mention "DELETE operation detected"

#### Test 7: Neo4j-Specific Syntax (Should Fail)

```bash
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the id of all projects"}' | jq '.'
```

**Expected Result**:
- `success`: false (if LLM generates `id(p)` instead of `p.id`)
- `verification_result.kuzu_compatibility_passed`: false
- `verification_result.issues`: Should mention "Neo4j-specific function 'id()'"

### Method 3: Python Script

Create `test_text_to_cypher.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_query(query: str):
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    response = requests.post(
        f"{BASE_URL}/graph/query",
        json={"query": query}
    )

    result = response.json()

    print(f"Success: {result.get('success')}")
    print(f"Cypher Query: {result.get('cypher_query')}")
    print(f"Row Count: {result.get('row_count')}")
    print(f"Confidence: {result.get('confidence')}")

    if result.get('success'):
        print(f"Results: {json.dumps(result.get('rows'), indent=2)}")
    else:
        print(f"Error: {result.get('error')}")
        print(f"Verification Issues: {result.get('verification_result', {}).get('issues')}")

# Run tests
test_query("How many projects are in the database?")
test_query("List all structural walls")
test_query("Count beams by level")
test_query("Show me walls in project 25-01-161")
```

Run it:

```bash
python test_text_to_cypher.py
```

## Debugging

### Check Server Logs

In DEBUG_MODE, the server logs all generated Cypher queries:

```
[TEXT_TO_CYPHER] ================================================================================
[TEXT_TO_CYPHER] 🔍 GENERATED CYPHER QUERY:
[TEXT_TO_CYPHER] MATCH (p:Project) RETURN count(p) AS project_count
[TEXT_TO_CYPHER] 💭 Reasoning: Simple count aggregation query for all Project nodes.
[TEXT_TO_CYPHER] 📊 Confidence: 1.0
[TEXT_TO_CYPHER] ================================================================================
[CYPHER_VERIFIER] 🛡️ Verifying Cypher query...
[CYPHER_VERIFIER] ✅ Safety check passed: No write operations detected
[CYPHER_VERIFIER] ✅ KuzuDB compatibility check passed
[TEXT_TO_CYPHER] ✅ Cypher query approved by verification agent
[TEXT_TO_CYPHER] ⚡ Executing Cypher query...
[KUZU_DB] 🔍 Executing READ query: MATCH (p:Project) RETURN count(p) AS project_count...
[TEXT_TO_CYPHER] ✅ Cypher executed successfully, 1 documents created
```

### Common Issues

#### 1. "Graph database access is only available in DEBUG_MODE"

**Problem**: `DEBUG_MODE` is not enabled.

**Solution**: Set `DEBUG_MODE=True` in `.env` and restart the server.

#### 2. "Kuzu manager not available"

**Problem**: KuzuDB failed to initialize.

**Solution**: Check that the database path exists and has proper permissions:
```bash
ls -la /home/proffessorq/Work/Sid-Master-Repo/Backend/nodes/DBRetrieval/data/kuzu_db
```

#### 3. "No results found for the graph database query"

**Problem**: Query executed successfully but returned no results.

**Solution**: This is normal if the data doesn't match the query. Check:
- Is the database populated? Run `MATCH (n) RETURN count(n)` via `/graph/cypher`
- Is the project name correct? Project names are case-sensitive

#### 4. "Neo4j-specific syntax detected"

**Problem**: LLM generated Neo4j-specific Cypher (e.g., `id(node)` instead of `node.id`)

**Solution**: This is working as expected! The verifier is catching incompatible syntax. The LLM should learn from examples to avoid this.

#### 5. LLM Generated Invalid JSON

**Problem**: LLM response couldn't be parsed as JSON.

**Solution**: The assistant has a fallback to extract Cypher from markdown code blocks. If this fails repeatedly, check the LLM configuration in `config/llm_instances.py`.

## Verification Checklist

Before moving to Phase 3, verify all of these work:

- [ ] Server starts successfully with DEBUG_MODE=True
- [ ] `/graph/schema` endpoint returns table list
- [ ] `/graph/query` endpoint accepts POST requests
- [ ] Simple count query ("How many projects?") succeeds
- [ ] List query ("List all projects") succeeds
- [ ] Structural query ("Show me structural walls") succeeds
- [ ] Project-specific query works
- [ ] Aggregation query works
- [ ] Write operations are REJECTED (DELETE, CREATE, etc.)
- [ ] Neo4j-specific syntax is REJECTED (id(), labels(), etc.)
- [ ] DEBUG_MODE logs show generated Cypher queries
- [ ] Response includes verification_result with all 5 checks
- [ ] Latency is reasonable (< 5 seconds for typical queries)

## Next Steps

Once all tests pass:

1. ✅ Phase 2.3 is complete
2. 🔄 Move to Phase 3: Integrate with RAG Router
3. 🔄 Phase 4: Create Graph Query Node
4. 🔄 Phase 5: Merge Graph Results with Vector Results
5. 🔄 Phase 6: End-to-End Testing

## Example Success Response

A successful query should look like this:

```json
{
  "success": true,
  "cypher_query": "MATCH (p:Project) RETURN p.name AS ProjectName, p.createdAt AS CreatedDate ORDER BY p.createdAt DESC LIMIT 10",
  "verification_result": {
    "approved": true,
    "safety_passed": true,
    "schema_passed": true,
    "syntax_passed": true,
    "kuzu_compatibility_passed": true,
    "issues": [],
    "warnings": [],
    "corrected_query": null,
    "reasoning": "Query is safe, valid, and KuzuDB-compatible"
  },
  "columns": ["ProjectName", "CreatedDate"],
  "rows": [
    ["Project A", "2024-01-15T10:30:00Z"],
    ["Project B", "2024-01-14T09:20:00Z"],
    ...
  ],
  "row_count": 10,
  "reasoning": "User requested a list of projects sorted by creation date. Query retrieves project names and timestamps.",
  "confidence": 0.95,
  "latency_ms": 1250.5,
  "error": null
}
```

## Contact

If you encounter issues not covered in this guide, check:
- `Backend/KUZU_COMPATIBILITY_NOTES.md` - KuzuDB vs Neo4j syntax differences
- `Backend/KUZU_INTEGRATION_PLAN.md` - Overall integration plan
- Server logs in DEBUG_MODE
