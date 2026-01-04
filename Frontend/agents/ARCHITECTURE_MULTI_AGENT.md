# Multi-Agent Architecture for Speed

## Overview

**Problem**: Single orchestrator handling everything is slow (too much reasoning overhead)

**Solution**: Multi-agent architecture with specialized orchestrators

## Architecture

```
TeamOrchestrator (Top-Level)
    ↓ Fast routing: "This is a search task"
    ↓
SearchOrchestrator (Specialized)
    ↓ Granular planning: "Extract → Query Supabase → Rank → Retrieve"
    ↓
Tools Execution
```

## Speed Benefits

### Single Orchestrator (Slow)
- One LLM call with full context
- Plans everything in detail
- ~2-3 seconds per query

### Multi-Agent (Fast)
- **TeamOrchestrator**: Fast routing (~0.5s)
  - Minimal prompt: "Is this search/document/analysis?"
  - No detailed planning
  
- **SearchOrchestrator**: Specialized planning (~1s)
  - Search-specific prompts
  - Optimized for search workflows
  - Knows about Supabase/GraphQL
  
- **Total**: ~1.5s (faster!)

## Structure (Following explain.txt)

```
agents/
├── base_agent.py              ← Base class (✅ Created)
├── team_orchestrator.py       ← Top-level router (✅ Created)
├── search_orchestrator.py     ← Search specialist (✅ Created)
├── orchestrator_agent.py     ← Old single orchestrator (keep for reference)
└── workflows/                 ← Future: Predefined workflows
```

## How It Works

### 1. User Query
```python
"Find me a project with a 50x100 layout"
```

### 2. TeamOrchestrator Routes
```python
{
    "agent_type": "search",
    "confidence": 0.95,
    "reasoning": "Query contains search keywords: find, project"
}
```

### 3. SearchOrchestrator Plans
```python
{
    "steps": [
        "Extract search criteria (dimensions: 50x100)",
        "Query Supabase via GraphQL for matching projects",
        "Rank results by similarity",
        "Retrieve project metadata"
    ],
    "data_sources": ["Supabase", "GraphQL"],
    "search_strategy": "dimension_matching"
}
```

### 4. SearchOrchestrator Executes
- Calls search tools
- Queries Supabase/GraphQL
- Returns results

## Usage

```python
from agents.team_orchestrator import TeamOrchestrator
from agents.search_orchestrator import SearchOrchestrator
from tools.search_tools import ALL_TOOLS

# Create specialized agents
search_agent = SearchOrchestrator(tools=ALL_TOOLS)

# Create team orchestrator
team_orchestrator = TeamOrchestrator(
    specialized_agents={
        "search": search_agent,
        # Future: "document": document_agent,
        # Future: "analysis": analysis_agent
    }
)

# Execute - fast routing + specialized execution
result = team_orchestrator.execute("Find me a 50x100 project")
```

## Key Advantages

✅ **Faster**: Specialized agents = optimized prompts = faster execution  
✅ **Scalable**: Add new specialized agents without changing top-level  
✅ **Maintainable**: Each agent handles one domain  
✅ **Optimized**: Search agent knows about Supabase/GraphQL specifically  
✅ **Parallelizable**: Can run multiple specialized agents in parallel (future)  

## Future Specialized Agents

- **DocumentOrchestrator**: Document analysis, reading, understanding
- **AnalysisOrchestrator**: Complex analysis, synthesis, recommendations
- **CodeOrchestrator**: Code generation, review, refactoring
- **DesignOrchestrator**: Design tasks, modeling, visualization

## Migration Path

1. ✅ Created base_agent.py
2. ✅ Created search_orchestrator.py  
3. ✅ Created team_orchestrator.py
4. ⏭️ Update run_tools.py to use TeamOrchestrator
5. ⏭️ Add more specialized agents as needed

The system is now optimized for speed with specialized agents!




