# 🚀 Getting the Fact Engine Service Running

## Step-by-Step Instructions

### 1. **Check Your Environment**
Make sure your `.env` file is in the parent directory (`GraphQL-MCP/.env`) with:
- `GRAPHQL_ENDPOINT`
- `GRAPHQL_TOKEN`
- `OPENAI_API_KEY`

### 2. **Start the Service**
```bash
cd fact_engine_service
python3 main.py
```

You should see:
```
✅ Semantic planner initialized
✅ Fact executor initialized (GraphQL: True)
✅ Answer composer initialized
INFO:     Application startup complete.
```

### 3. **Test GraphQL Connection First** (IMPORTANT!)
Before running a full query, test that GraphQL works:

```bash
curl http://localhost:8000/test-graphql
```

**Expected response:**
```json
{
  "status": "success",
  "project": "Some Project Name",
  "objects_found": 10,
  ...
}
```

**If this fails**, the GraphQL connection is broken. Check:
- Your `.env` file has correct `GRAPHQL_ENDPOINT` and `GRAPHQL_TOKEN`
- The GraphQL server is accessible
- Your token has permissions

### 4. **Test a Simple Query**
Once GraphQL test passes, try a query:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any columns?"}'
```

**What happens:**
1. **Planning** (fast, ~1-2 seconds) - Converts question to FactPlan
2. **Executing** (this is where it might hang) - Queries GraphQL for 1 project
3. **Composing** (fast, ~1-2 seconds) - Creates answer

### 5. **If It Hangs During Execution**

Check the service logs. You should see:
```
Processing project 1/1: [project name]
Getting root object for project...
Found X objects
```

**If it hangs at "Getting root object":**
- GraphQL query is taking too long
- Check your GraphQL endpoint is responding
- Try the `/test-graphql` endpoint again

**If it hangs at "Found X objects":**
- The fact extraction is taking too long
- This is normal for large datasets
- Wait up to 3 minutes (timeout is set)

### 6. **Increase Project Limit (Once Working)**

Once it works with 1 project, you can increase:

Edit `fact_engine_service/executor/executor.py`:
```python
max_projects = 10  # Increase from 1 to 10, then 100, etc.
```

### 7. **Enable Parallel Processing (Once Working)**

Edit `fact_engine_service/executor/executor.py`:
```python
use_parallel = True  # Change from False to True
```

## Troubleshooting

### Service Won't Start
- Check Python version: `python3 --version` (needs 3.8+)
- Install dependencies: `pip3 install -r requirements.txt`
- Check `.env` file exists and has all required variables

### GraphQL Test Fails
- Verify endpoint URL is correct
- Verify token is valid
- Check network connectivity to GraphQL server

### Query Times Out
- Reduce `max_projects` to 1
- Check GraphQL server performance
- Increase timeout in `main.py` (currently 180 seconds)

### Service Hangs Forever
- Check logs for error messages
- Try `/test-graphql` endpoint first
- Restart the service
- Check if GraphQL server is responding

## Quick Test Commands

```bash
# Health check
curl http://localhost:8000/health

# Test GraphQL
curl http://localhost:8000/test-graphql

# List available facts
curl http://localhost:8000/facts

# Run a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any timber columns?"}'
```

## What Changed

1. **Added timeout** - Queries now timeout after 3 minutes instead of hanging forever
2. **Async execution** - GraphQL queries run in thread pool to avoid blocking
3. **Test endpoint** - `/test-graphql` lets you verify connection before running full queries
4. **Reduced projects** - Starts with 1 project for testing
5. **Better logging** - More detailed logs to see where it's stuck


