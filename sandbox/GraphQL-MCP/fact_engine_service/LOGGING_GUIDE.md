# Logging Guide

## How to See Logs

The detailed logs from the Fact Engine Service appear in the **terminal where you started the service**, not in the test script output.

### Step 1: Start the Service

In Terminal 1:
```bash
cd fact_engine_service
python main.py
```

You should see:
```
INFO - Logging configured at level: INFO
================================================================================
Service starting - logs will appear below
================================================================================
✅ Semantic planner initialized
✅ Fact executor initialized (GraphQL: True)
✅ Answer composer initialized
```

### Step 2: Run Tests

In Terminal 2:
```bash
cd fact_engine_service
python3 test_service.py -q "Do we have any timber columns?"
```

### Step 3: Watch Terminal 1

When you run a query, you'll see detailed logs in Terminal 1 (the service terminal):

```
================================================================================
MAIN: Starting query processing
MAIN: Question: Do we have any timber columns?
MAIN: Step 1 - Planning phase
================================================================================
PLANNER: Starting planning phase
PLANNER: Question: Do we have any timber columns?
PLANNER: Generated FactPlan details:
  - Scope: project
  - Number of filters: 2
  ...
================================================================================
EXECUTOR: Starting execution phase
EXECUTOR: Phase 1 - Candidate Discovery
EXECUTOR: GraphQL discovery - fetching projects
...
```

## Log Prefixes

- `MAIN:` - Overall pipeline orchestration
- `PLANNER:` - Semantic planning (question → FactPlan)
- `EXECUTOR:` - Fact execution (candidate discovery, fact extraction)
- `COMPOSER:` - Answer composition (facts → human-readable answer)

## Log Levels

Set in `.env`:
- `LOG_LEVEL=INFO` - Shows INFO, WARNING, ERROR (default)
- `LOG_LEVEL=DEBUG` - Shows everything including DEBUG messages

## Troubleshooting

### No logs appearing?

1. **Restart the service** - The service needs to be restarted to pick up new logging code
2. **Check the service terminal** - Logs appear where you ran `python main.py`, not in the test script
3. **Verify log level** - Make sure `LOG_LEVEL=INFO` or `LOG_LEVEL=DEBUG` in your `.env` file
4. **Check uvicorn** - If using `uvicorn` directly, logs should still appear in that terminal

### Test logging is working

Run:
```bash
python3 check_logs.py
```

You should see test log messages. If you don't, there's an issue with your terminal output.


