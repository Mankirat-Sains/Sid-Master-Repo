# Testing Guide for Fact Engine Service

## Quick Start Testing

### 1. Setup Environment

The service will automatically read the `.env` file from the parent directory:
```
/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/GraphQL-MCP/.env
```

Make sure your `.env` contains:
- `GRAPHQL_ENDPOINT` - Your Speckle GraphQL endpoint
- `GRAPHQL_AUTH_TOKEN` - Authentication token (if required)
- `OPENAI_API_KEY` - Your OpenAI API key
- Database credentials (if using PostgreSQL)

### 2. Install Dependencies

```bash
cd fact_engine_service
pip install -r requirements.txt
```

### 3. Start the Service

```bash
# From fact_engine_service directory
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
✅ Semantic planner initialized
✅ Fact executor initialized (GraphQL: True)
✅ Answer composer initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Testing Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "planner": true,
    "executor": true,
    "composer": true,
    "graphql": true
  }
}
```

### 2. List Available Facts

```bash
curl http://localhost:8000/facts
```

Expected response:
```json
{
  "available_facts": [
    "element_type",
    "material",
    "section",
    "level",
    "orientation",
    "system_role",
    "project_summary"
  ]
}
```

### 3. Test a Simple Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Do we have any timber columns?"
  }'
```

Expected response structure:
```json
{
  "answer": {
    "answer": "Yes — Building A contains 12 timber columns...",
    "explanation": "...",
    "confidence": 0.85,
    "supporting_facts": [...],
    "project_count": 1
  },
  "fact_plan": {
    "scope": "project",
    "filters": [
      {"fact": "element_type", "op": "=", "value": "column"},
      {"fact": "material", "op": "=", "value": "timber"}
    ],
    "aggregations": [...],
    "outputs": [...]
  },
  "fact_result": {
    "projects": {...},
    "execution_time_ms": 1234.5,
    "total_elements_processed": 150
  }
}
```

## Test Cases

### Test 1: Element Type Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What types of structural elements do we have?"}'
```

### Test 2: Material Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What materials are used in our projects?"}'
```

### Test 3: Combined Filter
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many steel beams are in our projects?"}'
```

### Test 4: Level-Based Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What elements are on Level 2?"}'
```

### Test 5: System Role Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any lateral systems using timber?"}'
```

## Python Testing Script

Create a test script `test_service.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_facts():
    """Test facts endpoint"""
    response = requests.get(f"{BASE_URL}/facts")
    print("Available Facts:", response.json())
    assert response.status_code == 200

def test_query(question):
    """Test a query"""
    response = requests.post(
        f"{BASE_URL}/query",
        json={"question": question}
    )
    print(f"\nQuestion: {question}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data['answer']['answer']}")
        print(f"Confidence: {data['answer']['confidence']}")
        print(f"Projects: {data['answer']['project_count']}")
        print(f"Execution Time: {data['fact_result']['execution_time_ms']}ms")
        print(f"Elements Processed: {data['fact_result']['total_elements_processed']}")
    else:
        print(f"Error: {response.text}")
    
    return response

if __name__ == "__main__":
    # Test health
    test_health()
    
    # Test facts
    test_facts()
    
    # Test queries
    test_query("Do we have any timber columns?")
    test_query("What materials are used?")
    test_query("How many steel beams are there?")
```

Run it:
```bash
python test_service.py
```

## Debugging

### Check Logs

The service logs to console. Look for:
- `✅` - Successful initialization
- `❌` - Errors
- `INFO` - General information
- `ERROR` - Error messages

### Common Issues

1. **GraphQL Connection Failed**
   - Check `GRAPHQL_ENDPOINT` in `.env`
   - Verify endpoint is accessible
   - Check authentication token

2. **No Projects Found**
   - Verify you have access to projects
   - Check GraphQL authentication

3. **LLM Errors**
   - Verify `OPENAI_API_KEY` is set
   - Check API key is valid
   - Ensure you have credits

4. **Import Errors**
   - Make sure you're in the `fact_engine_service` directory
   - Run: `pip install -r requirements.txt`

### Enable Debug Logging

Set in `.env`:
```
LOG_LEVEL=DEBUG
```

## Testing GraphQL Connection

Test GraphQL connection directly:

```python
from db.graphql_client import graphql_client

# Test getting projects
projects = graphql_client.get_projects(limit=5)
print(f"Found {len(projects)} projects")
for p in projects:
    print(f"  - {p.get('name')} ({p.get('id')})")

# Test canonical discovery
if projects:
    project_id = projects[0].get("id")
    objects = graphql_client.discover_candidates_canonical(
        project_id=project_id,
        speckle_type_filter="Column"
    )
    print(f"\nFound {len(objects)} column candidates")
```

## Performance Testing

Test with different question complexities:

```bash
# Simple query
time curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have columns?"}'

# Complex query
time curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the material distribution across all projects by element type?"}'
```

## Expected Behavior

1. **Fast Response**: < 5 seconds for simple queries
2. **Accurate Facts**: Extracted facts match actual data
3. **Confidence Scores**: Between 0.0 and 1.0
4. **Evidence**: Each fact includes evidence paths
5. **Composed Answers**: Human-readable, well-explained

## Next Steps

Once basic testing works:
1. Test with your actual Speckle projects
2. Try more complex questions
3. Verify fact extraction accuracy
4. Check confidence scores make sense
5. Review evidence paths for correctness


