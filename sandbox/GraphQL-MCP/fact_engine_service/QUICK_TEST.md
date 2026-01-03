# Quick Testing Guide

## Step 1: Start the Service

```bash
cd fact_engine_service
python main.py
```

Wait for:
```
✅ Semantic planner initialized
✅ Fact executor initialized (GraphQL: True)
✅ Answer composer initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Test in Another Terminal

### Option A: Use the Test Script

```bash
cd fact_engine_service
python test_service.py
```

This will:
- ✅ Check service health
- ✅ List available facts
- ✅ Run 4 test queries
- ✅ Show summary

### Option B: Manual Testing with curl

**1. Health Check:**
```bash
curl http://localhost:8000/health
```

**2. List Facts:**
```bash
curl http://localhost:8000/facts
```

**3. Ask a Question:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any timber columns?"}'
```

**4. More Test Questions:**
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

## Step 3: Check Results

Each query returns:
- **answer**: Human-readable answer
- **confidence**: 0.0 to 1.0 score
- **fact_plan**: The structured plan (JSON)
- **fact_result**: Extracted facts with evidence

## Troubleshooting

**Service won't start?**
- Check `.env` file in parent directory has required keys
- Make sure dependencies are installed: `pip install -r requirements.txt`

**GraphQL connection failed?**
- Verify `GRAPHQL_ENDPOINT` in `.env`
- Check `GRAPHQL_AUTH_TOKEN` if required

**No projects found?**
- Verify GraphQL authentication
- Check you have access to projects

**LLM errors?**
- Verify `OPENAI_API_KEY` is set
- Check API key is valid

## Expected Output

Successful query should return:
```json
{
  "answer": {
    "answer": "Yes — Building A contains 12 timber columns...",
    "confidence": 0.85,
    "project_count": 1
  },
  "fact_plan": {...},
  "fact_result": {
    "execution_time_ms": 1234.5,
    "total_elements_processed": 150
  }
}
```

## Next Steps

Once basic tests pass:
1. Try your own questions
2. Check fact extraction accuracy
3. Review confidence scores
4. Examine evidence paths


