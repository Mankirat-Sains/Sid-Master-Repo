# Phase 3: State Management Refactoring Plan

## Goals

1. **Keep ParentState** (rename to OrchestrationState for clarity)
2. **Remove RAGState completely** - it's causing confusion
3. **Each subgraph has its own state**:
   - `DBRetrievalState` ✅ (already exists)
   - `DesktopAgentState` (create new)
   - `WebCalcsState` (create new)
   - `BuildingModelGenState` (create new)
4. **Only key results flow to parent** - subgraphs return minimal dicts

## Current State Analysis

### ParentState (100 lines)
- **Keep**: Core orchestration fields (session_id, user_query, selected_routers, etc.)
- **Keep**: Results aggregation fields (db_retrieval_result, webcalcs_result, etc.)
- **Review**: Desktop-specific fields (should move to DesktopAgentState)
- **Review**: Doc generation fields (should move to DesktopAgentState)

### RAGState (73 lines) - **DELETE**
- Extends DBRetrievalState (wrong inheritance)
- Duplicates ParentState fields
- Used by ALL subgraphs (wrong - each should have own state)

### DBRetrievalState (87 lines) - **KEEP & CLEAN**
- Already subgraph-specific ✅
- Used only by DBRetrieval subgraph ✅
- May have unused fields to review

## New Architecture

```
OrchestrationState (Parent - minimal, orchestration only)
    │
    ├── DBRetrievalState (internal to DBRetrieval subgraph)
    ├── DesktopAgentState (internal to DesktopAgent subgraph)
    ├── WebCalcsState (internal to WebCalcs subgraph)
    └── BuildingModelGenState (internal to BuildingModelGen subgraph)
```

## Implementation Steps

### Step 1: Rename ParentState → OrchestrationState
- Rename file: `parent_state.py` → `orchestration_state.py`
- Rename class: `ParentState` → `OrchestrationState`
- Update all imports

### Step 2: Create Subgraph-Specific States
- Create `DesktopAgentState` (extract desktop fields from OrchestrationState)
- Create `WebCalcsState` (minimal state for calculations)
- Create `BuildingModelGenState` (minimal state for model generation)

### Step 3: Remove RAGState
- Delete `rag_state.py`
- Update all imports to use OrchestrationState or subgraph states
- Remove `_convert_to_rag_state()` helper

### Step 4: Update Subgraph Wrappers
- Simplify wrappers - no more state conversion
- Extract only needed fields from OrchestrationState
- Return minimal dicts with results

### Step 5: Update Graph Builder
- Use OrchestrationState throughout
- Remove RAGState references
- Simplify state handling

### Step 6: Review & Clean Fields
- Remove unused fields from each state
- Ensure fields are actually needed
- Document what each field does

## Field Analysis

### OrchestrationState - Keep These:
- ✅ `session_id`, `user_query`, `original_question` (core)
- ✅ `messages`, `conversation_history` (persistence)
- ✅ `selected_routers` (routing)
- ✅ `images_base64`, `project_filter` (shared inputs)
- ✅ `db_retrieval_result`, `webcalcs_result`, `desktop_result` (results)
- ✅ `execution_trace` (debugging)

### OrchestrationState - Move to DesktopAgentState:
- `selected_app`, `operation_type`, `file_path`
- `desktop_tools`, `desktop_reasoning`
- `workflow`, `task_type`, `doc_type`, `section_type`
- `doc_request`, `requires_desktop_action`
- All `desktop_*` fields (plan_steps, workspace, etc.)
- `doc_generation_result`, `doc_generation_warnings`

### OrchestrationState - Remove (unused/duplicate):
- `verification_result` (check if used)
- `desktop_action_plan` (move to DesktopAgentState)
- `desktop_steps` (move to DesktopAgentState)
- `desktop_execution` (move to DesktopAgentState)

## Files to Modify

### Create New Files:
1. `Backend/models/orchestration_state.py` (rename from parent_state.py)
2. `Backend/models/desktop_agent_state.py` (new)
3. `Backend/models/webcalcs_state.py` (new)
4. `Backend/models/building_model_gen_state.py` (new)

### Delete Files:
1. `Backend/models/rag_state.py` ❌
2. `Backend/models/parent_state.py` (renamed)

### Update Files (27 files):
- `Backend/main.py`
- `Backend/graph/builder.py`
- `Backend/nodes/router_dispatcher.py`
- `Backend/nodes/plan.py`
- `Backend/graph/subgraphs/*.py` (all subgraphs)
- `Backend/nodes/DesktopAgent/WordAgent/*.py` (WordAgent files)
- `Backend/api_server.py`
- Test files

## Risk Assessment

**Risk Level**: MEDIUM
- Many files need updates
- State conversions need careful handling
- Need to ensure no data loss

**Mitigation**:
- Update in phases
- Test after each phase
- Keep git commits atomic
- Verify all imports work

---

**Status**: Ready to execute
**Estimated Time**: 2-3 hours
**Priority**: High (removes major confusion)
