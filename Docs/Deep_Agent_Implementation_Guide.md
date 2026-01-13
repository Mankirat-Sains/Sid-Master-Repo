# Implementation Guide: Transforming Sidian into Optimal Deep Agent Architecture

Based on the detailed audit and target architecture, here's a comprehensive implementation guide:

## Phase 1: Foundation & Low-Risk Improvements (Week 1)

### 1.1 Fix Conversation History & State Alignment
**Files to modify:**
- `Backend/nodes/DBRetrieval/SQLdb/correct.py`
- `Backend/models/rag_state.py`
- `Backend/api_server.py`

**Implementation:**
```python
# In correct.py, replace current message handling:
def node_correct(state: DBRetrievalState) -> dict:
    # ... existing code ...
    
    # Update conversation_history alongside messages
    current_messages = state.get("messages", [])
    conversation_history = state.get("conversation_history", [])
    
    # Add assistant response to both
    assistant_msg = AIMessage(content=final_response, metadata=metadata)
    updated_messages = current_messages + [assistant_msg]
    updated_history = conversation_history + [assistant_msg]
    
    return {
        "messages": updated_messages[-MAX_CONVERSATION_HISTORY*2:],
        "conversation_history": updated_history,
        # ... other updates
    }
```

### 1.2 Extend Execution Tracing to Subgraphs
**Files to modify:**
- `Backend/graph/builder.py`
- `Backend/graph/subgraphs/db_retrieval_subgraph.py`
- `Backend/graph/subgraphs/desktop_agent_subgraph.py`

**Implementation:**
```python
# Create a decorator in builder.py
def wrap_subgraph_node(node_name: str):
    def decorator(func):
        async def wrapper(state: dict):
            # Record entry
            trace_entry = {
                "node": node_name,
                "timestamp": datetime.utcnow().isoformat(),
                "state_snapshot": {k: str(v)[:100] for k, v in state.items() if k not in ['messages', 'retrieved_docs']}
            }
            
            # Run node
            result = await func(state) if asyncio.iscoroutinefunction(func) else func(state)
            
            # Record exit
            trace_entry.update({
                "duration_ms": ...,
                "result_keys": list(result.keys()) if result else []
            })
            
            # Append to execution_trace
            execution_trace = state.get("execution_trace", [])
            execution_trace.append(trace_entry)
            result["execution_trace"] = execution_trace
            
            return result
        return wrapper
    return decorator

# Apply to all subgraph nodes
@wrap_subgraph_node("rag_plan_router")
async def node_rag_plan_router(state): ...
```

## Phase 2: Enable Quality Gates (Week 2)

### 2.1 Turn On Verifier with Bounded Scope
**Files to modify:**
- `Backend/nodes/DBRetrieval/SQLdb/verify.py`
- `.env` configuration

**Implementation:**
```python
# verify.py - Enable with safety checks
USE_VERIFIER = os.getenv("USE_VERIFIER", "True").lower() == "true"
MAX_VERIFIER_TOKENS = 2000  # Keep lightweight

def node_verify(state: DBRetrievalState) -> dict:
    if not USE_VERIFIER:
        return {"needs_fix": False}
    
    # Lightweight verification only
    checks = [
        _check_citations_present(state),
        _check_answer_grounded(state),
        _check_no_hallucinations(state),
    ]
    
    needs_fix = any(check["fails"] for check in checks)
    issues = [issue for check in checks for issue in check.get("issues", [])]
    
    return {
        "needs_fix": needs_fix,
        "verification_issues": issues,
        "verification_checks": checks
    }

def _check_citations_present(state) -> dict:
    """Check answer has citations to retrieved docs"""
    answer = state.get("answer", "")
    citations = state.get("answer_citations", [])
    retrieved = state.get("retrieved_docs", {}).get("project", [])
    
    if not citations and retrieved and len(answer) > 100:
        return {"fails": True, "issues": ["No citations in lengthy answer"]}
    return {"fails": False}
```

### 2.2 Enable Grading with Limits
**Files to modify:**
- `Backend/nodes/DBRetrieval/SQLdb/grade.py`
- Add token counting helper

**Implementation:**
```python
# grade.py - Enable with token limits
USE_GRADER = os.getenv("USE_GRADER", "True").lower() == "true"
MAX_DOCS_TO_GRADE = 10
MAX_GRADER_TOKENS = 4000

def node_grade(state: DBRetrievalState) -> dict:
    if not USE_GRADER:
        # Pass through with simple filtering
        return _lightweight_filter(state)
    
    # Token-aware grading
    docs = state.get("retrieved_docs", {}).get("project", [])
    if not docs:
        return {"graded_docs": {}}
    
    # Limit docs and tokens
    limited_docs = docs[:MAX_DOCS_TO_GRADE]
    total_tokens = sum(count_tokens(d["content"]) for d in limited_docs)
    
    if total_tokens > MAX_GRADER_TOKENS:
        # Fall back to heuristic filter
        return _heuristic_grade(state)
    
    # Run full grader
    return _run_llm_grader(state, limited_docs)

def _heuristic_grade(state):
    """Fast heuristic grading when token count is high"""
    docs = state.get("retrieved_docs", {}).get("project", [])
    
    # Simple scoring: relevance based on keyword overlap
    query = state.get("query_plan", {}).get("query", state.get("user_query", ""))
    query_terms = set(query.lower().split())
    
    scored_docs = []
    for doc in docs[:15]:  # Limit
        content = doc.get("content", "").lower()
        score = len(query_terms.intersection(set(content.split()))) / max(len(query_terms), 1)
        scored_docs.append({**doc, "relevance_score": score})
    
    # Take top 8 by score
    scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
    return {"graded_docs": {"project": scored_docs[:8]}}
```

## Phase 3: Deep Desktop Agent Transformation (Week 3-4)

### 3.1 Create Deep Desktop Loop Node
**New files:**
- `Backend/nodes/DesktopAgent/deep_desktop_loop.py`
- `Backend/graph/subgraphs/deep_desktop_subgraph.py`

**Implementation:**
```python
# deep_desktop_loop.py
class DeepDesktopLoop:
    """Deep agent wrapper that runs think-act-observe cycles"""
    
    def __init__(self):
        self.tools = self._initialize_tools()
        self.max_iterations = 10
        self.workspace_base = Path("/workspace")
        self.memories_base = Path("/memories")
        
    async def run(self, state: RAGState) -> dict:
        """Main deep agent loop"""
        # Initialize workspace
        thread_id = state.get("session_id", "default")
        workspace_dir = self.workspace_base / thread_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial plan
        plan = await self._create_plan(state, workspace_dir)
        
        # Execute plan step-by-step
        results = []
        for step_idx, step in enumerate(plan.get("steps", [])):
            if step_idx >= self.max_iterations:
                break
                
            # Think: Analyze step
            thought = await self._think_about_step(step, state, results)
            
            # Act: Execute with potential interrupt
            action_result = await self._execute_with_interrupts(step, thought, workspace_dir)
            
            # Observe: Process result
            observation = await self._observe_result(action_result, workspace_dir)
            
            results.append({
                "step": step,
                "thought": thought,
                "action": action_result,
                "observation": observation
            })
            
            # Check completion
            if observation.get("is_complete", False):
                break
        
        return {
            "desktop_action_result": results,
            "output_artifact_ref": self._package_results(results, workspace_dir),
            "requires_desktop_action": False  # Completed
        }
    
    async def _execute_with_interrupts(self, step, thought, workspace_dir):
        """Execute step with interrupt gates for destructive actions"""
        action_type = step.get("action")
        
        # Destructive actions require approval
        destructive_actions = {"edit_file", "write_file", "delete_file", "materialize_doc"}
        if action_type in destructive_actions:
            # Create interrupt for approval
            interrupt_data = {
                "action": action_type,
                "details": step,
                "thought": thought,
                "workspace_context": self._get_workspace_snapshot(workspace_dir)
            }
            
            # Raise interrupt - will be caught by LangGraph
            raise GraphInterrupt(
                f"Approval required for {action_type}",
                data=interrupt_data,
                resume_signal="approved"
            )
        
        # Safe actions execute immediately
        return await self._call_tool(step)
```

### 3.2 Integrate Deep Loop into Desktop Subgraph
**Files to modify:**
- `Backend/graph/subgraphs/desktop_agent_subgraph.py`
- `Backend/models/rag_state.py`

**Implementation:**
```python
# desktop_agent_subgraph.py - Updated structure
def build_desktop_agent_subgraph():
    workflow = StateGraph(RAGState)
    
    # Nodes
    workflow.add_node("desktop_router", node_desktop_router)
    workflow.add_node("deep_desktop_loop", DeepDesktopLoop().run)  # NEW
    workflow.add_node("doc_generation", doc_generation_subgraph)  # Kept as tool
    workflow.add_node("finish", node_finish)
    
    # Edges
    workflow.set_entry_point("desktop_router")
    
    # Route to deep loop for all desktop actions
    workflow.add_edge("desktop_router", "deep_desktop_loop")
    
    # Deep loop can call docgen as a tool, then finish
    workflow.add_conditional_edges(
        "deep_desktop_loop",
        lambda s: "doc_generation" if s.get("task_type", "").startswith("doc_") else "finish",
        {
            "doc_generation": "doc_generation",
            "finish": "finish"
        }
    )
    
    workflow.add_edge("doc_generation", "finish")
    
    return workflow.compile()

# rag_state.py - Add deep agent fields
class RAGState(DBRetrievalState, total=False):
    # ... existing fields ...
    
    # Deep desktop agent fields
    desktop_plan_steps: List[Dict]
    desktop_current_step: int
    desktop_workspace_files: List[str]
    desktop_memories: List[Dict]
    desktop_interrupt_pending: bool
    desktop_approved_actions: List[str]
    
    # Tool execution logs
    tool_execution_log: List[Dict]
    large_output_refs: Dict[str, str]  # file references for big outputs
```

### 3.3 Convert DocGen to Tool in Deep Loop
**Files to modify:**
- `Backend/desktop_agent/agents/doc_generation/`
- `Backend/nodes/DesktopAgent/tools/docgen_tool.py` (new)

**Implementation:**
```python
# docgen_tool.py
class DocGenTool:
    """Wrapper that makes docgen subgraph callable as a tool"""
    
    @tool
    async def generate_document_section(
        self,
        doc_request: Dict,
        context: Dict,
        workspace_dir: Path
    ) -> Dict:
        """Tool version of docgen subgraph"""
        
        # Write context to workspace for docgen
        context_file = workspace_dir / "docgen_context.json"
        context_file.write_text(json.dumps(context))
        
        # Call existing docgen logic
        from ..doc_generation.section_generator import SectionGenerator
        generator = SectionGenerator()
        
        result = await generator.generate(
            doc_request=doc_request,
            context_path=str(context_file),
            output_dir=workspace_dir
        )
        
        # Evict large outputs to files
        if len(result.get("draft_text", "")) > 5000:
            text_file = workspace_dir / f"doc_output_{uuid4()}.md"
            text_file.write_text(result["draft_text"])
            result["draft_text_ref"] = str(text_file)
            result["draft_text"] = result["draft_text"][:1000] + "... [truncated]"
        
        return result
```

## Phase 4: Implement Middleware Features (Week 5)

### 4.1 Workspace vs Memories Strategy
**New files:**
- `Backend/persistence/workspace_manager.py`
- `Backend/persistence/memory_store.py`

**Implementation:**
```python
# workspace_manager.py
class WorkspaceManager:
    """Manages ephemeral workspace files"""
    
    def __init__(self, base_path: Path = Path("/workspace")):
        self.base = base_path
        
    def get_thread_workspace(self, thread_id: str) -> Path:
        """Get or create workspace for thread"""
        workspace = self.base / thread_id
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Clean old files (keep last 24 hours)
        self._clean_old_files(workspace)
        
        return workspace
    
    def write_workspace_file(self, thread_id: str, filename: str, content: str) -> Path:
        """Write to workspace, returns path"""
        workspace = self.get_thread_workspace(thread_id)
        filepath = workspace / filename
        filepath.write_text(content)
        return filepath
    
    def _clean_old_files(self, workspace: Path):
        """Clean files older than retention period"""
        retention_hours = 24
        cutoff = time.time() - (retention_hours * 3600)
        
        for file in workspace.iterdir():
            if file.stat().st_mtime < cutoff:
                file.unlink()

# memory_store.py  
class MemoryStore:
    """Manages durable memories across threads"""
    
    def __init__(self, store_backend: str = "supabase"):
        self.backend = self._init_backend(store_backend)
        
    def store_memory(self, key: str, value: Dict, tags: List[str] = None):
        """Store durable memory"""
        memory = {
            "id": str(uuid4()),
            "key": key,
            "value": value,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "access_count": 0
        }
        
        return self.backend.store("memories", memory)
    
    def retrieve_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant memories"""
        return self.backend.search("memories", query, limit)
```

### 4.2 Tool Result Eviction & Summarization
**Files to modify:**
- `Backend/utils/tool_eviction.py` (new)
- Update all tool-calling nodes

**Implementation:**
```python
# tool_eviction.py
class ToolResultEvictor:
    """Handles large tool output eviction to files"""
    
    MAX_INLINE_SIZE = 3000  # characters
    SUMMARY_LENGTH = 500
    
    def process_result(self, tool_name: str, result: Any, workspace_dir: Path) -> Dict:
        """Process tool result, evicting large outputs to files"""
        
        # Convert to string for size check
        if isinstance(result, dict):
            result_str = json.dumps(result)
        else:
            result_str = str(result)
        
        if len(result_str) <= self.MAX_INLINE_SIZE:
            return {"inline": result}
        
        # Too large - write to file and create summary
        filename = f"{tool_name}_{uuid4().hex[:8]}.json"
        filepath = workspace_dir / filename
        filepath.write_text(result_str)
        
        # Create summary
        summary = self._create_summary(result, result_str)
        
        return {
            "evicted": True,
            "file_ref": str(filepath),
            "summary": summary,
            "size_chars": len(result_str),
            "original_type": type(result).__name__
        }
    
    def _create_summary(self, result, result_str: str) -> str:
        """Create intelligent summary of large result"""
        if isinstance(result, list):
            return f"List with {len(result)} items: {result_str[:self.SUMMARY_LENGTH]}..."
        elif isinstance(result, dict):
            keys = list(result.keys())[:5]
            return f"Dict with keys: {keys} ..."
        else:
            return result_str[:self.SUMMARY_LENGTH] + "..."
```

### 4.3 Enhanced Logging & Observability
**Files to modify:**
- `Backend/observability/tracing.py` (new)
- Update `builder.py` and all nodes

**Implementation:**
```python
# tracing.py
class StructuredTracer:
    """Structured logging for deep agent operations"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events = []
        
    def log_tool_call(self, tool_name: str, args: Dict, result: Dict):
        """Log structured tool call"""
        event = {
            "type": "tool_call",
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args_hash": hashlib.md5(json.dumps(args).encode()).hexdigest()[:8],
            "result_summary": self._summarize_result(result),
            "duration_ms": ...,
            "success": result.get("success", True)
        }
        self.events.append(event)
        
        # Also write to CSV for analysis
        self._write_to_csv(event)
    
    def log_decision(self, node: str, decision: str, reasoning: str):
        """Log agent decisions"""
        event = {
            "type": "decision",
            "node": node,
            "decision": decision,
            "reasoning": reasoning[:500]  # Truncate
        }
        self.events.append(event)
    
    def get_trace(self) -> Dict:
        """Get full trace for response"""
        return {
            "session_id": self.session_id,
            "events": self.events,
            "summary": self._generate_summary()
        }
```

## Phase 5: Integration & Testing (Week 6)

### 5.1 Update API Layer for Deep Agent
**Files to modify:**
- `Backend/api_server.py`
- `Backend/main.py`

**Implementation:**
```python
# api_server.py - Update streaming response
async def chat_stream(request: ChatRequest):
    # ... existing setup ...
    
    # Initialize deep agent workspace if needed
    if request.data_sources and "desktop" in request.data_sources:
        workspace_mgr = WorkspaceManager()
        workspace_dir = workspace_mgr.get_thread_workspace(session_id)
        
        # Inject workspace info into state
        initial_state["workspace_dir"] = str(workspace_dir)
        initial_state["memory_store"] = MemoryStore()
    
    # Stream with enhanced tracing
    async for update in graph.astream(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
        stream_mode=["updates", "custom", "messages", "tool_calls"]  # NEW
    ):
        # Process tool call events
        if "tool_calls" in update:
            for tool_call in update["tool_calls"]:
                yield json.dumps({
                    "type": "tool_call",
                    "tool": tool_call["name"],
                    "status": tool_call.get("status", "executing"),
                    "data": tool_call.get("data", {})
                })
        
        # ... existing streaming logic ...
```

### 5.2 Create Configuration & Environment
**.env.example additions:**
```bash
# Deep Agent Settings
DEEP_AGENT_ENABLED=true
MAX_DEEP_AGENT_ITERATIONS=10
WORKSPACE_RETENTION_HOURS=24
MAX_INLINE_TOOL_RESULT=3000

# Interrupt Settings
INTERRUPT_DESTRUCTIVE_ACTIONS=true
INTERRUPT_APPROVAL_TIMEOUT=300

# Memory Settings
MEMORY_STORE_BACKEND=supabase  # or 'sqlite', 'postgres'
MEMORY_RETENTION_DAYS=30
```

## Implementation Priority & Risk Mitigation

### Week 1-2: Safe Foundation
1. **Fix conversation history** - Low risk, immediate quality improvement
2. **Extend execution tracing** - Low risk, better observability
3. **Enable verifier with bounds** - Medium risk, test with sample queries

### Week 3-4: Core Transformation  
4. **Create deep desktop loop** - High risk, implement in parallel path first
5. **Add workspace/memory separation** - Medium risk, backward compatible

### Week 5-6: Polish & Integration
6. **Implement tool eviction** - Low risk, progressive enhancement
7. **Add structured logging** - Low risk, additive
8. **Integrate interrupts** - Medium risk, mirror existing code verification pattern

## Desktop Deep Agent Implementation Tracker

### Phase 1: Foundation & Low-Risk Improvements
- **Conversation History & State Alignment**  
  - Purpose: Keep `messages` and `conversation_history` synchronized with sliding windows for persistence and rewriting context.  
  - Files: `Backend/nodes/DBRetrieval/SQLdb/correct.py`, `Backend/api_server.py`, `Backend/models/rag_state.py`, `Backend/graph/builder.py`, `Backend/graph/subgraphs/db_retrieval_subgraph.py`, `Backend/graph/subgraphs/desktop_agent_subgraph.py`.  
  - Implementation: Normalize legacy history, sync user/assistant turns, enforce windowing, propagate execution trace from subgraphs, widen trace typing.  
  - Status: ✅ Completed.  
  - Evidence: `correct.py` updates both lists with shared windows; API seeds both lists; subgraphs wrapped for tracing; traces merged upward; `rag_state` trace typing widened.  
  - Dependencies: Baseline LangGraph state flow. Later phases rely on consistent state/tracing.
- **Execution Tracing Extension to Subgraphs**  
  - Purpose: Capture per-node execution across subgraphs for observability.  
  - Files: Above plus `Backend/graph/tracing.py`.  
  - Implementation: Wrapper decorator records entry/exit, snapshots, result keys; traces merged back to parent.  
  - Status: ✅ Completed.  
  - Evidence: `graph/tracing.py` added; subgraph nodes wrapped; trace merge in wrappers.  
  - Dependencies: Used by later deep agent tracing.

### Phase 2: Enable Quality Gates
- **Verifier with Bounded Scope**  
  - Purpose: Lightweight answer checks with token caps and simple heuristics.  
  - Files: `Backend/nodes/DBRetrieval/SQLdb/verify.py`, `Backend/utils/token_counter.py`, `Backend/config/settings.py`, `.env.example`.  
  - Implementation: Env-flagged verifier, MAX_VERIFIER_TOKENS, citation/grounding/hallucination checks, skips on long answers.  
  - Status: ✅ Completed.  
  - Evidence: `USE_VERIFIER` defaults true; token counter added; verify returns `verification_checks/issues`.  
  - Dependencies: Token counter; settings.
- **Grader with Limits and Fallback**  
  - Purpose: Token-aware document grading with heuristic fallback when over budget.  
  - Files: `Backend/nodes/DBRetrieval/SQLdb/grade.py`, `Backend/utils/token_counter.py`, `Backend/config/settings.py`, `.env.example`.  
  - Implementation: Env-flagged grader, doc/token limits, heuristic keyword overlap fallback, preserves code/coop handling.  
  - Status: ✅ Completed.  
  - Evidence: `USE_GRADER` defaults true; MAX_DOCS_TO_GRADE/MAX_GRADER_TOKENS enforced; heuristic path logs selection.  
  - Dependencies: Token counter; settings.

### Phase 3A: State & Workspace Foundation
- **Workspace Manager & State Extensions**  
  - Purpose: Provide per-thread ephemeral storage and deep agent state fields.  
  - Files: `Backend/persistence/workspace_manager.py`, `Backend/models/rag_state.py`, `Backend/config/settings.py`, `.env.example`, `Backend/persistence/__init__.py`.  
  - Implementation: Workspace CRUD/retention/snapshots; RAGState extended with deep desktop fields; settings/env defaults for workspace/iteration/interrupt thresholds.  
  - Status: ✅ Completed.  
  - Evidence: Workspace manager class; new RAGState fields; settings/env entries for workspace/interrupt/tool result limits.  
  - Dependencies: Required by deep loop.

### Phase 3B: Deep Desktop Loop Core
- **Think-Act-Observe Loop**  
  - Purpose: Replace single-shot desktop actions with iterative deep loop, planning, execution, observation.  
  - Files: `Backend/nodes/DesktopAgent/deep_desktop_loop.py`.  
  - Implementation: Plans via LLM, iterates up to MAX_DEEP_AGENT_ITERATIONS, basic tools (read/write/list), packages results/artifacts.  
  - Status: ✅ Completed.  
  - Evidence: DeepDesktopLoop class with planning, execution, observation, artifact packaging; compiled successfully.  
  - Dependencies: Workspace manager; settings; RAGState fields.

### Phase 3C: Interrupt Integration
- **Destructive Action Interrupts**  
  - Purpose: Gate destructive actions with approval via GraphInterrupt.  
  - Files: `Backend/nodes/DesktopAgent/deep_desktop_loop.py`.  
  - Implementation: Detects destructive actions, raises GraphInterrupt with context unless approved; edit/delete tools added; action_ids tracked.  
  - Status: ✅ Completed.  
  - Evidence: Interrupt gating in `_execute_step`, `_is_destructive_action`, `_create_interrupt_data`; edit/delete tools implemented.  
  - Dependencies: Interrupt-aware router; RAGState approval lists; to be wired via API.

### Phase 3D: DocGen Tool Wrapper & Output Eviction
- **DocGen as Tool with Eviction**  
  - Purpose: Make docgen callable as a tool and evict large outputs to workspace.  
  - Files: `Backend/nodes/DesktopAgent/tools/docgen_tool.py`, `Backend/nodes/DesktopAgent/tools/__init__.py`, `Backend/utils/tool_eviction.py`, `Backend/nodes/DesktopAgent/deep_desktop_loop.py`.  
  - Implementation: DocGen tool wrapper calls section_generator (fallback mock), prepares context, evicts large drafts, integrates evictor; deep loop updated to use tool list and evict large outputs.  
  - Status: ✅ Completed.  
  - Evidence: Docgen tool class; tool eviction utility; deep loop uses docgen_tool/get_evictor and includes generate_document in tools.  
  - Dependencies: Workspace manager; settings MAX_INLINE_TOOL_RESULT.

### Phase 3E: Integration
- **Deep Desktop Subgraph**  
  - Purpose: Wrap deep desktop loop in a LangGraph subgraph.  
  - Files: `Backend/graph/subgraphs/deep_desktop_subgraph.py`.  
  - Implementation: StateGraph(RAGState) with single node deep_desktop_loop → END; call wrapper.  
  - Status: ✅ Completed.  
  - Evidence: File added; compiled subgraph with invoke wrapper.  
  - Dependencies: DeepDesktopLoop; RAGState.
- **Feature-Flag Routing in Desktop Agent Subgraph**  
  - Purpose: Route desktop flows to deep loop when enabled, fallback to docgen otherwise.  
  - Files: `Backend/graph/subgraphs/desktop_agent_subgraph.py`.  
  - Implementation: StateGraph now uses RAGState; conditional edges include deep_desktop when DEEP_AGENT_ENABLED; state normalized to RAGState with defaults; traces merged.  
  - Status: ✅ Completed.  
  - Evidence: Imports DEEP_AGENT_ENABLED and deep_desktop_subgraph; routing updated; RAGState conversion helper.  
  - Dependencies: deep_desktop_subgraph; RAGState extensions.
- **Main Graph Builder Wiring**  
  - Purpose: Wire deep desktop into parent graph build; avoid circular imports.  
  - Files: `Backend/graph/builder.py`.  
  - Implementation: Not yet done; import deep desktop subgraph inside build_graph and ensure desktop path uses updated subgraph.  
  - Status: ⬜ Not Started.  
  - Evidence: N/A.  
  - Dependencies: desktop_agent_subgraph updates; deep_desktop_subgraph.
- **Integration Helper Utilities**  
  - Purpose: Helper for feature flag checks, interrupt handling, resume-after-approval, action summaries.  
  - Files: `Backend/utils/deep_agent_integration.py`.  
  - Implementation: Not yet done; utility functions for API and flow orchestration.  
  - Status: ⬜ Not Started.  
  - Evidence: N/A.  
  - Dependencies: Interrupt data from deep loop.
- **API Interrupt Approval Endpoint**  
  - Purpose: Allow user to approve destructive actions and resume execution.  
  - Files: `Backend/api_server.py`.  
  - Implementation: Not yet done; `/approve-action` endpoint to add action_id to `desktop_approved_actions` and resume graph.  
  - Status: ⬜ Not Started.  
  - Evidence: N/A.  
  - Dependencies: Interrupt data; integration helper; builder wiring.
- **Resume-After-Approval Flow**  
  - Purpose: Resume graph execution after approval with updated state.  
  - Files: `Backend/api_server.py`, integration helper.  
  - Implementation: Not yet done; load checkpoint, update approvals, re-invoke graph.  
  - Status: ⬜ Not Started.  
  - Evidence: N/A.  
  - Dependencies: Approval endpoint; builder wiring; deep agent state fields.
- **Documentation & Rollout Updates**  
  - Purpose: Document deep agent behavior, interrupts, workspace, feature flag usage.  
  - Files: `.env.example`, docs (TBD).  
  - Implementation: Partially done via env additions; narrative docs pending.  
  - Status: 🟡 Partially Completed.  
  - Evidence: Env example updated with deep agent settings; no narrative docs yet.  
  - Dependencies: Final wiring and API behavior.

### Progress Summary
- Completion: ~70% of desktop deep agent implementation done (core loop, interrupts, docgen tool, eviction, subgraph, feature-flag routing).
- Deep agent capabilities already present: iterative think–act–observe loop; workspace-backed tools; docgen as tool with eviction; destructive action interrupts; feature-flagged routing to deep path.
- Remaining for production readiness: main builder wiring; integration helpers; approval/resume API flow; full docs/rollout guidance; end-to-end testing of both flag paths and interrupt/approval lifecycle.

### Current Status & Testing Notes (Source: this implementation log)
- Completed: Phase 1, Phase 2, Phase 3A–3D, and Phase 3E (deep_desktop_subgraph + feature-flag routing in desktop_agent_subgraph). These components compile and are integrated under the feature flag.
- Pending: Builder wiring, integration helper utilities, approval/resume API endpoint, resume-after-approval flow, full documentation/rollout narrative.
- Testing performed: Module-level `py_compile` on new/modified Python files; no end-to-end or runtime desktop deep-agent flows executed yet due to pending wiring/API resume.
- Testing needed:
  - Feature flag toggle: deep path vs. legacy docgen.
  - Interrupt flow: destructive action triggers GraphInterrupt; approve via API and resume.
  - Resume-after-approval: checkpoint/load, add approved action_ids, re-invoke graph.
  - Workspace behavior: per-thread file writes and retention cleanup.
  - Eviction behavior: large docgen outputs (>MAX_INLINE_TOOL_RESULT) produce file refs with summaries.

## Testing Strategy

1. **Unit tests** for each new component (workspace manager, evictor, tracer)
2. **Integration tests** with sample desktop actions
3. **Shadow mode** - Run new deep agent alongside existing for comparison
4. **Canary deployment** - Enable for specific users/tasks first

## Rollback Plan

1. Keep existing `desktop_agent_subgraph` as fallback
2. Use feature flags to toggle between old and new implementation
3. Maintain backward compatibility in state schema
4. Detailed metrics comparison before full switch
