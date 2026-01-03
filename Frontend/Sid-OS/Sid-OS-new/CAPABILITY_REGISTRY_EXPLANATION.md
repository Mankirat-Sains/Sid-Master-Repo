# Capability Registry System - Explanation

## Problem Solved

Previously, the system was making decisions about data sources (like "supabase_metadata", "rag_documents") that were **hardcoded in LLM prompts** without checking if they actually exist. This could lead to:
- Planning to use tables that don't exist
- Selecting data sources that aren't configured
- Making assumptions about available tools

## Solution: Capability Registry

Created a **dynamic capability discovery system** that:
1. **Discovers available tools** from `localagent/tools/`
2. **Checks available vector stores/tables** from Supabase
3. **Provides this information to the planning LLM** so decisions are based on reality
4. **Filters planning results** to only include available sources

## Files Created/Modified

### 1. `localagent/core/capability_registry.py` (NEW)
- **Purpose:** Discovers and registers all available system capabilities
- **Key Classes:**
  - `ToolCapability`: Represents a single tool
  - `TableCapability`: Represents a database table/vector store
  - `CapabilityRegistry`: Main registry that discovers everything

**How it works:**
- Imports tools from `localagent.tools`
- Checks Supabase vector stores (`vs_smart`, `vs_code`, `vs_coop`, `vs_large`)
- Provides methods to get available data sources, tools, and tables
- Converts registry to planning context for LLM

### 2. `localagent/agents/team_orchestrator.py` (MODIFIED)
- **Changes:**
  - Imports capability registry
  - Gets available capabilities before planning
  - Includes capability context in LLM prompt
  - **Filters data sources** to only include available ones
  - Generates high-level plan display (like `retrieve_db_info.plan.md`)

**Key improvements:**
- Planning prompt now includes: "IMPORTANT: Only select from AVAILABLE data sources"
- LLM receives actual capability context
- Data sources are filtered after LLM response
- High-level plan is generated and displayed

### 3. `localagent/agents/search_orchestrator.py` (MODIFIED)
- **Changes:**
  - Uses capability registry to know what's available
  - Generates detailed tactical plan (like Cursor's step-by-step)
  - Shows which tables will be searched and why

**Key improvements:**
- Tactical plan shows exact table names (`smart_chunks`, `code_chunks`, etc.)
- Explains why each table is being searched
- Shows which tools will be used

### 4. `backend/main.py` (MODIFIED)
- **Changes:**
  - Displays high-level plan from TeamOrchestrator
  - Shows planning information in logs

## How It Works

### Step 1: Discovery
```python
registry = get_registry()
# Discovers:
# - Available tools (from localagent.tools)
# - Available vector stores (from Supabase connection)
# - Which tables are actually initialized
```

### Step 2: Planning with Context
```python
# LLM receives:
system_prompt = """
Available data sources:
- rag_documents: ONLY if project_db is available
- rag_codes: ONLY if code_db is available
...
CURRENT SYSTEM CAPABILITIES:
{capability_context}
"""
```

### Step 3: Filtering
```python
# After LLM responds, filter to only available sources
filtered_sources = [
    src for src in requested_sources 
    if src in available_data_sources
]
```

### Step 4: Display
```python
# High-level plan shown to user:
## 🎯 Execution Plan
1. Identify search criteria
2. Search project database
3. Rank results
...
```

## Benefits

1. **No Hardcoding:** Decisions based on actual available resources
2. **Self-Aware:** System knows what it can and cannot do
3. **Graceful Degradation:** If a table isn't available, it's not selected
4. **Transparency:** User sees what's actually being used
5. **Maintainable:** Add new tools/tables → automatically discovered

## Example Flow

**Query:** "Find me a project with a sandwich wall"

1. **Registry Discovery:**
   - Finds: `vs_smart` available → `rag_documents` available
   - Finds: `vs_code` not available → `rag_codes` not available
   - Finds: Tools: `extract_search_criteria`, `search_projects_by_dimensions`, etc.

2. **Planning:**
   - LLM receives: "Available: rag_documents, calculation_tools"
   - LLM selects: `["rag_documents"]` (only available source)
   - System filters: Ensures only `rag_documents` is used

3. **Execution:**
   - Searches `smart_chunks` table (because `rag_documents` → `project_db=True`)
   - Does NOT try to search `code_chunks` (not available)

4. **Display:**
   - High-level plan: Shows steps 1-6
   - Tactical plan: Shows `smart_chunks` table will be searched
   - Tool logs: Shows which tools are actually used

## Future Enhancements

1. **Dynamic Tool Registration:** Tools register themselves
2. **Health Checks:** Verify tables are actually queryable
3. **Performance Metrics:** Track which tools/tables are used most
4. **Capability Caching:** Cache discovery results for performance




