# Deep Agent Architecture

## Overview
The desktop agent now runs as a deep, iterative agent that plans, executes, and observes in cycles, guarded by human-in-the-loop interrupts for destructive actions. It layers workspace management, tool eviction, and structured tracing on top of the existing LangGraph orchestration.

## Architecture Components
### 1) Deep Desktop Loop
- Think–Act–Observe cycles with iterative planning (bounded by `MAX_DEEP_AGENT_ITERATIONS`)
- Tool execution driven by the deep loop (docgen callable as a tool)
- State tracked in `RAGState` and persisted via the graph checkpointer

### 2) Workspace Management
- Per-thread ephemeral workspaces at `WORKSPACE_BASE_PATH`
- File CRUD + workspace snapshots; automatic cleanup after `WORKSPACE_RETENTION_HOURS`

### 3) Interrupt System
- Destructive actions gated by `GraphInterrupt`
- API returns structured interrupt payloads; approvals handled via `/approve-action`
- Approved actions tracked in `desktop_approved_actions`

### 4) Tool Framework
- DocGen exposed as a callable tool inside the deep loop
- Tool result eviction when outputs exceed `MAX_INLINE_TOOL_RESULT`
- Structured logging and trace merging for parent/subgraphs

## State Management
### RAGState Extensions (desktop/deep agent)
- Plan & execution: `desktop_plan_steps`, `desktop_current_step`, `desktop_iteration_count`
- Workspace: `desktop_workspace_dir`, `desktop_workspace_files`, `desktop_context`
- Safety: `desktop_interrupt_pending`, `desktop_interrupt_data`, `desktop_approved_actions`
- Tooling: `tool_execution_log`, `large_output_refs`, `desktop_loop_result`
- Tracing: `execution_trace`, `execution_trace_verbose`

## Integration Points
### Main Graph (`Backend/graph/builder.py`)
- Uses `RAGState` for compatibility with deep desktop fields
- Wraps all nodes to merge traces from subgraphs
- Conditional routing to desktop_agent with feature flag support

### Desktop Agent Subgraph (`Backend/graph/subgraphs/desktop_agent_subgraph.py`)
- Routes to deep desktop loop when `DEEP_AGENT_ENABLED`
- Normalizes ParentState → RAGState and back

### Deep Desktop Loop (`Backend/nodes/DesktopAgent/deep_desktop_loop.py`)
- Think/act/observe iterations, workspace management, docgen tool calls
- Interrupts raised for destructive actions when `INTERRUPT_DESTRUCTIVE_ACTIONS` is true

### API Layer (`Backend/api_server.py`)
- `/chat/stream` emits `interrupt` SSE payloads on `GraphInterrupt`
- `/approve-action` records approvals, clears interrupt flags, and resumes the graph

## Configuration
Key environment variables (see `.env.example`):
- `DEEP_AGENT_ENABLED`, `MAX_DEEP_AGENT_ITERATIONS`
- `WORKSPACE_BASE_PATH`, `WORKSPACE_RETENTION_HOURS`
- `INTERRUPT_DESTRUCTIVE_ACTIONS`, `INTERRUPT_APPROVAL_TIMEOUT`
- `MAX_INLINE_TOOL_RESULT`
- Feature flags: `ENABLE_DEEP_PLANNING`, `ENABLE_TOOL_EVICTION`, `ENABLE_AUTO_SUMMARIZATION`
