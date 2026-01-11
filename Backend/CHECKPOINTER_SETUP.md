# Checkpointer Setup - Following LangGraph Protocols

## Overview

The checkpointer follows LangGraph's official patterns for short-term memory (thread-level persistence). It supports multiple backends for different environments.

## Architecture

### LangGraph Protocol Compliance

✅ **Follows LangGraph's official patterns**:
- Uses `PostgresSaver.from_conn_string()` for production
- Uses `SqliteSaver` for local development
- Uses `InMemorySaver` for testing
- Calls `checkpointer.setup()` to initialize tables
- Passes checkpointer to `graph.compile(checkpointer=checkpointer)`
- Uses `thread_id` in config for conversation threads

### Reference
- [LangGraph Add Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [Postgres Checkpointer Example](https://docs.langchain.com/oss/python/langgraph/add-memory#example-using-postgres-checkpointer)

---

## Configuration

### Environment Variables

Set `CHECKPOINTER_TYPE` in your `.env` file:

```bash
# Development (in-memory, not persistent)
CHECKPOINTER_TYPE=memory

# Local development (file-based, persistent)
CHECKPOINTER_TYPE=sqlite
CHECKPOINT_DB_PATH=checkpoints.db  # Optional, defaults to checkpoints.db

# Production (database-backed, persistent) - Works with Supabase!
CHECKPOINTER_TYPE=postgres
# OR use 'supabase' as alias
CHECKPOINTER_TYPE=supabase

# Option 1: Direct Supabase connection string (recommended)
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Option 2: Explicit checkpointer database
CHECKPOINT_POSTGRES_URI=postgresql://user:password@localhost:5432/langgraph_checkpoints

# Option 3: Generic Postgres
POSTGRES_URI=postgresql://user:password@localhost:5432/langgraph_checkpoints

# Option 4: Auto-build from Supabase credentials (if SUPABASE_URL and SUPABASE_DB_PASSWORD are set)
# The checkpointer will automatically build the connection string from:
# - SUPABASE_URL (e.g., https://[project-ref].supabase.co)
# - SUPABASE_DB_PASSWORD (your database password)
```

---

## Installation

### For SQLite (Local Development)
```bash
pip install langgraph-checkpoint-sqlite
```

### For Postgres (Production)
```bash
pip install langgraph-checkpoint-postgres
pip install "psycopg[binary,pool]"  # Required dependency
```

---

## Usage

### How It Works

1. **Thread-Based Persistence**: Each `session_id` is a separate thread
   ```python
   config = {"configurable": {"thread_id": session_id}}
   ```

2. **Automatic State Saving**: LangGraph automatically saves state after each node execution

3. **State Recovery**: Load previous state using:
   ```python
   state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})
   ```

4. **Messages**: Stored in `RAGState.messages` (follows LangGraph's pattern: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`) and automatically persisted

### Example Flow

```python
# First invocation
graph.invoke(
    asdict(init_state),
    config={"configurable": {"thread_id": "user_123"}}
)

# Second invocation (same thread_id) - automatically loads previous state
graph.invoke(
    asdict(init_state),
    config={"configurable": {"thread_id": "user_123"}}  # Same thread_id
)
```

---

## Backend Comparison

| Backend | Type | Persistence | Use Case | Package |
|---------|------|-------------|----------|---------|
| `InMemorySaver` | In-memory | ❌ Lost on restart | Testing/Development | Built-in |
| `SqliteSaver` | File-based | ✅ Persistent | Local development | `langgraph-checkpoint-sqlite` |
| `PostgresSaver` | Database | ✅ Persistent | Production | `langgraph-checkpoint-postgres` |

---

## Production Setup

### Option 1: Supabase (Recommended for Production)

Supabase uses PostgreSQL, so the checkpointer works seamlessly with it!

1. **Get Your Supabase Database Connection String**:
   - Go to your Supabase project dashboard
   - Navigate to Settings → Database
   - Find "Connection string" → "Direct connection" or "Connection pooling"
   - Copy the connection string (it will look like: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`)

2. **Set Environment Variables**:
   ```bash
   # Option A: Direct connection string (recommended)
   CHECKPOINTER_TYPE=supabase
   SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   
   # Option B: Auto-build from existing Supabase credentials
   CHECKPOINTER_TYPE=supabase
   SUPABASE_URL=https://[project-ref].supabase.co
   SUPABASE_DB_PASSWORD=[your-database-password]
   ```

3. **Initialize Tables**:
   The checkpointer automatically calls `setup()` on first use, which creates the necessary tables in your Supabase database.

**Note**: The checkpointer will create tables in the same database as your Supabase project. Make sure your database user has CREATE TABLE permissions.

### Option 2: Standalone Postgres Database

1. **Create Database**:
   ```sql
   CREATE DATABASE langgraph_checkpoints;
   ```

2. **Set Environment Variable**:
   ```bash
   export POSTGRES_URI="postgresql://user:password@localhost:5432/langgraph_checkpoints"
   export CHECKPOINTER_TYPE=postgres
   ```

3. **Initialize Tables**:
   The checkpointer automatically calls `setup()` on first use, which creates the necessary tables.

### Connection String Format

```
postgresql://[user]:[password]@[host]:[port]/[database]?[options]
```

Example:
```
postgresql://postgres:postgres@localhost:5432/langgraph_checkpoints?sslmode=disable
```

---

## Verification

### Check if Checkpointer is Working

1. **Check Logs**: Look for initialization message:
   ```
   ✅ Postgres checkpointer initialized: postgresql://...
   ```

2. **Test Persistence**:
   - Make a query with `session_id="test_123"`
   - Restart the server
   - Make another query with same `session_id="test_123"`
   - Should load previous conversation history

3. **Check Database** (Postgres/Supabase):
   ```sql
   -- In Supabase SQL Editor or psql
   SELECT COUNT(*) FROM checkpoints;
   SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;
   SELECT * FROM checkpoints ORDER BY checkpoint_ns DESC LIMIT 5;
   ```

---

## Troubleshooting

### Issue: "langgraph-checkpoint-postgres not installed"
**Solution**: 
```bash
pip install langgraph-checkpoint-postgres "psycopg[binary,pool]"
```

### Issue: "Failed to initialize Postgres checkpointer"
**Solution**: 
- Check database connection string
- Verify database exists
- Check database permissions
- Falls back to InMemorySaver automatically

### Issue: "Tables may already exist" warning
**Solution**: This is normal - `setup()` is idempotent and safe to call multiple times.

### Issue: Conversation history lost on restart
**Solution**: 
- Make sure `CHECKPOINTER_TYPE` is not `memory`
- For production, use `CHECKPOINTER_TYPE=postgres`
- Verify `POSTGRES_URI` is set correctly

---

## Code Location

- **Checkpointer Implementation**: `Backend/graph/checkpointer.py`
- **Graph Builder**: `Backend/graph/builder.py` (uses `checkpointer` from `graph.checkpointer`)
- **State Loading**: `Backend/main.py` (loads previous state from checkpointer)
- **State Definition**: `Backend/models/rag_state.py` (`messages` field - follows LangGraph pattern)

---

## Next Steps

1. **For Production**: Set `CHECKPOINTER_TYPE=postgres` and configure `POSTGRES_URI`
2. **For Local Dev**: Set `CHECKPOINTER_TYPE=sqlite` (optional, defaults to memory)
3. **Monitor**: Check database size and implement TTL if needed
4. **Backup**: Include checkpointer database in your backup strategy
