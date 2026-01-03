# 🚀 Quick Start Guide

## Your GraphQL Endpoint
```
http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/graphql
```

## Step 1: Update Your .env File

Make sure your `.env` file in the parent directory (`GraphQL-MCP/.env`) has:

```bash
GRAPHQL_ENDPOINT=http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/graphql
GRAPHQL_AUTH_TOKEN=your_token_here
OPENAI_API_KEY=your_openai_key_here
```

**Note:** If you don't have a token, you might not need `GRAPHQL_AUTH_TOKEN` - try without it first.

## Step 2: Start the Service

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

## Step 3: Test GraphQL Connection

In a **new terminal**:

```bash
curl http://localhost:8000/test-graphql
```

**Expected:** JSON response with `"status": "success"`

**If it fails:**
- Check your `.env` file has the correct `GRAPHQL_ENDPOINT`
- Check if you need `GRAPHQL_AUTH_TOKEN` (some endpoints don't require it)
- Verify the endpoint URL is accessible

## Step 4: Run a Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any columns?"}'
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'"
✅ **FIXED** - This is now optional. The service will use GraphQL only.

### Service won't start
- Make sure you're in the `fact_engine_service` directory
- Check Python version: `python3 --version` (needs 3.8+)
- Install dependencies: `pip3 install -r requirements.txt`

### GraphQL test fails
- Verify your endpoint URL is correct
- Check if authentication is required
- Try accessing the endpoint in a browser to verify it's up

### Query times out
- The service processes 1 project at a time (for testing)
- First query may take 30-60 seconds
- If it takes > 3 minutes, you'll get a timeout error

## What Changed

1. ✅ Made `psycopg2` optional - service works with GraphQL only
2. ✅ Added timeout protection - queries timeout after 3 minutes
3. ✅ Added `/test-graphql` endpoint - test connection before queries
4. ✅ Reduced to 1 project for testing - faster initial tests


