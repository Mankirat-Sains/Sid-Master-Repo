# Test Your Running Service

Your service is now running! Here's how to test it:

## Quick Test (in a new terminal)

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. List Available Facts
```bash
curl http://localhost:8000/facts
```

### 3. Ask Your First Question
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any timber columns?"}'
```

## Or Use the Test Script

In a **new terminal window**, run:

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/GraphQL-MCP/fact_engine_service"
python3 test_service.py
```

## More Test Questions

Try these questions:

```bash
# What materials are used?
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What materials are used in our projects?"}'

# How many steel beams?
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many steel beams are there?"}'

# What element types?
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What types of structural elements do we have?"}'
```

## What to Expect

A successful response will look like:

```json
{
  "answer": {
    "answer": "Yes — Building A contains 12 timber columns...",
    "confidence": 0.85,
    "project_count": 1,
    "supporting_facts": [...]
  },
  "fact_plan": {
    "scope": "project",
    "filters": [...],
    "aggregations": [...]
  },
  "fact_result": {
    "execution_time_ms": 1234.5,
    "total_elements_processed": 150
  }
}
```

## Troubleshooting

**If you get connection errors:**
- Make sure the service is still running (check the terminal where you started it)
- The service should be on `http://localhost:8000`

**If queries take a long time:**
- First query may be slower (GraphQL connection setup)
- Complex queries may take 5-10 seconds

**If you get GraphQL errors:**
- Check your `.env` file has correct `GRAPHQL_ENDPOINT`
- Verify `GRAPHQL_AUTH_TOKEN` if required

