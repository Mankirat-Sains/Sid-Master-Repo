# Subgraph Architecture Recommendations

## Executive Summary

Based on the [LangGraph Subgraphs documentation](https://docs.langchain.com/oss/python/langgraph/use-subgraphs) and your current architecture, implementing subgraphs will significantly improve your system's **modularity, maintainability, observability, and scalability**. This document explains why and how.

---

## Why Subgraphs Will Improve Your System

### 1. **Better Encapsulation & Separation of Concerns**

**Current Problem:**
- All nodes are in a flat graph structure
- Capability branches (DBRetrieval, WebCalcs, DesktopAgent) are mixed with orchestration logic
- Hard to understand which nodes belong to which capability

**With Subgraphs:**
- Each capability branch becomes a self-contained subgraph
- Clear boundaries between different system components
- Matches your Architecture.md principle: "Separation of reasoning, execution, and retrieval"

### 2. **Independent State Management**

**Current Problem:**
- All nodes share the same `RAGState` with all possible fields
- WebCalcs and DesktopAgent nodes must know about RAG-specific fields (retrieved_docs, graded_docs, etc.)
- State pollution: fields from one capability affect others

**With Subgraphs:**
- Each subgraph can have its own state schema
- DBRetrieval subgraph manages: `retrieved_docs`, `graded_docs`, `final_answer`
- WebCalcs subgraph manages: `web_tools`, `calculation_results`
- DesktopAgent subgraph manages: `desktop_tools`, `execution_logs`
- Parent graph only needs: `user_query`, `selected_routers`, `session_id`

**Example:**
```python
# Parent graph state (minimal)
class ParentState(TypedDict):
    user_query: str
    selected_routers: List[str]
    session_id: str
    # Results from subgraphs
    rag_result: Optional[str]
    web_result: Optional[Dict]
    desktop_result: Optional[Dict]

# DBRetrieval subgraph state (specialized)
class DBRetrievalState(TypedDict):
    user_query: str
    query_plan: Optional[Dict]
    retrieved_docs: List[Document]
    graded_docs: List[Document]
    final_answer: Optional[str]
    # ... all RAG-specific fields
```

### 3. **Improved Observability & Debugging**

**Current Problem:**
- When debugging, you see all nodes in one flat structure
- Hard to trace which nodes belong to which capability
- Streaming output mixes all capabilities together

**With Subgraphs:**
- LangGraph provides subgraph-aware streaming: `graph.stream(..., subgraphs=True)`
- You can see exactly which subgraph is executing
- Better error isolation: errors in WebCalcs don't pollute DBRetrieval logs
- Can inspect subgraph state independently (when interrupted)

**Example Output:**
```
((), {'plan': {'selected_routers': ['rag', 'web']}})
(('rag_subgraph:abc123',), {'retrieve': {'retrieved_docs': [...]}})
(('rag_subgraph:abc123',), {'grade': {'graded_docs': [...]}})
(('web_subgraph:def456',), {'web_router': {'web_tools': ['calculator']}})
((), {'rag_subgraph': {'final_answer': '...'}})
```

### 4. **Independent Persistence & Checkpointing**

**Current Problem:**
- Single checkpointer for entire graph
- Can't have different persistence strategies per capability
- All capabilities share the same thread_id

**With Subgraphs:**
- Each subgraph can have its own checkpointer (if needed)
- Useful for multi-agent systems where each agent needs separate memory
- Parent graph checkpointer automatically propagates to children
- Can resume individual subgraphs independently

### 5. **Better Testability**

**Current Problem:**
- To test DBRetrieval pipeline, you must set up entire graph
- Hard to mock other capabilities
- Integration tests are complex

**With Subgraphs:**
- Test each subgraph independently
- Mock parent graph state easily
- Unit test capability branches in isolation
- Integration tests can test subgraph composition

### 6. **Easier Parallel Development**

**Current Problem:**
- All developers work on same flat graph
- Merge conflicts in `builder.py` are common
- Changes to one capability affect others

**With Subgraphs:**
- Different teams can work on different subgraphs
- As long as subgraph interface (input/output) is respected, teams can work independently
- Matches your Architecture.md: "Distributing development: when you want different teams to work on different parts of the graph independently"

### 7. **Cleaner Graph Structure**

**Current Problem:**
- `builder.py` has 10+ nodes in flat structure
- Complex conditional routing logic
- Hard to visualize the system architecture

**With Subgraphs:**
- Parent graph becomes simple: `plan → router_dispatcher → [subgraphs] → END`
- Each subgraph is a black box from parent's perspective
- Matches your Architecture.md: "Major Capability Branches" are now actual subgraphs

---

## Recommended Subgraph Structure

Based on your Architecture.md and current code, here are the recommended subgraphs:

### 1. **DBRetrieval Subgraph** (Highest Priority)

**Purpose:** Complete RAG pipeline for database retrieval

**Nodes:**
- `rag_plan` (or keep in parent, see below)
- `rag_router` (or keep in parent, see below)
- `retrieve`
- `grade`
- `answer`
- `verify`
- `correct`

**State Schema:**
```python
class DBRetrievalState(TypedDict):
    user_query: str
    query_plan: Optional[Dict]
    data_sources: Dict[str, bool]
    data_route: Optional[Literal["smart", "large"]]
    project_filter: Optional[str]
    expanded_queries: List[str]
    retrieved_docs: List[Document]
    retrieved_code_docs: List[Document]
    retrieved_coop_docs: List[Document]
    graded_docs: List[Document]
    graded_code_docs: List[Document]
    graded_coop_docs: List[Document]
    final_answer: Optional[str]
    answer_citations: List[Dict]
    code_answer: Optional[str]
    code_citations: List[Dict]
    coop_answer: Optional[str]
    coop_citations: List[Dict]
    answer_support_score: float
    needs_fix: bool
    corrective_attempted: bool
    follow_up_questions: List[str]
    follow_up_suggestions: List[str]
    # Image processing (if used in RAG context)
    images_base64: Optional[List[str]]
    image_description: Optional[str]
    image_similarity_results: List[Dict]
    use_image_similarity: bool
```

**Why This First:**
- Most complex capability branch
- Has clear pipeline: retrieve → grade → answer → verify → correct
- Most state fields belong here
- Will demonstrate biggest improvement

**Implementation Approach:**
- Use "Invoke a graph from a node" pattern (different state schemas)
- Transform parent state → DBRetrieval state before invoking
- Transform DBRetrieval result → parent state after completion

### 2. **Image Processing Subgraph** (Medium Priority)

**Purpose:** Handle image similarity search pipeline

**Nodes:**
- `generate_image_embeddings` (or `generate_image_description`)
- `image_similarity_search`

**State Schema:**
```python
class ImageProcessingState(TypedDict):
    images_base64: List[str]
    user_query: str
    image_description: Optional[str]
    image_similarity_results: List[Dict]
    use_image_similarity: bool
```

**Why:**
- Currently mixed into main graph
- Can be reused by multiple capabilities
- Clear, isolated functionality

**Implementation Approach:**
- Can be invoked from DBRetrieval subgraph OR parent graph
- Use "Add a graph as a node" if sharing state keys with parent
- Use "Invoke a graph from a node" if completely separate

### 3. **WebCalcs Subgraph** (Medium Priority)

**Purpose:** Web calculation tools orchestration

**Nodes:**
- `web_router`
- (Future: calculator execution, SkyCiv, Jabacus nodes)

**State Schema:**
```python
class WebCalcsState(TypedDict):
    user_query: str
    web_tools: List[str]
    web_reasoning: str
    calculation_results: Optional[Dict]  # Future
```

**Why:**
- Currently just a router, but will grow
- Architecture.md says it will have multiple tools
- Should be independent from DBRetrieval

**Implementation Approach:**
- Use "Invoke a graph from a node" (different state)
- Currently simple, but will expand

### 4. **DesktopAgent Subgraph** (Medium Priority)

**Purpose:** Desktop application interaction

**Nodes:**
- `desktop_router`
- (Future: Excel Agent, Word Agent, Revit Agent nodes)

**State Schema:**
```python
class DesktopAgentState(TypedDict):
    user_query: str
    desktop_tools: List[str]
    desktop_reasoning: str
    execution_logs: Optional[List[Dict]]  # Future
    action_results: Optional[Dict]  # Future
```

**Why:**
- Architecture.md describes multiple desktop agents
- Needs separate state for execution tracking
- High-risk actions need isolation

**Implementation Approach:**
- Use "Invoke a graph from a node" (different state)
- Can have its own checkpointer for action history

### 5. **BuildingModelGen Subgraph** (Future)

**Purpose:** Building model generation and modification

**Nodes:**
- (To be implemented per Architecture.md)

**Why:**
- Architecture.md describes this as a major capability
- Will have its own verification logic
- Should be completely independent

---

## Best Practices & Implementation Guidelines

### 1. **State Schema Design**

**DO:**
- Keep parent state minimal (only shared fields)
- Each subgraph has its own specialized state
- Transform state at boundaries (parent ↔ subgraph)

**DON'T:**
- Share all state keys between parent and subgraphs (defeats the purpose)
- Put capability-specific fields in parent state

**Example:**
```python
# Parent state (minimal)
class ParentState(TypedDict):
    user_query: str
    session_id: str
    selected_routers: List[str]
    # Results aggregated from subgraphs
    rag_result: Optional[str]
    web_result: Optional[Dict]
    desktop_result: Optional[Dict]

# Transform function
def call_rag_subgraph(state: ParentState) -> dict:
    # Transform to subgraph state
    rag_input = {
        "user_query": state["user_query"],
        "session_id": state["session_id"],
        # ... other RAG-specific fields
    }
    rag_output = rag_subgraph.invoke(rag_input)
    
    # Transform back to parent state
    return {
        "rag_result": rag_output["final_answer"],
        # ... other aggregated results
    }
```

### 2. **Subgraph Invocation Pattern**

**Use "Invoke a graph from a node" when:**
- Subgraph has different state schema (recommended for your use case)
- You want complete isolation
- Subgraph doesn't need to share state keys with parent

**Use "Add a graph as a node" when:**
- Subgraph shares some state keys with parent
- You want subgraph to directly update parent state
- Simpler state management (but less isolation)

**Recommendation:** Use "Invoke a graph from a node" for all your capability branches (DBRetrieval, WebCalcs, DesktopAgent) because they have different concerns and state.

### 3. **Persistence Strategy**

**Parent Graph:**
- Provide checkpointer when compiling parent graph
- LangGraph automatically propagates to subgraphs
- All subgraphs share parent's checkpointer by default

**Independent Subgraph Memory (if needed):**
- Compile subgraph with its own checkpointer: `subgraph.compile(checkpointer=True)`
- Useful for multi-agent systems where each agent needs separate memory
- Example: DesktopAgent might want to track its own action history separately

**Recommendation:** Start with shared checkpointer (automatic propagation). Add independent checkpointers only if you need separate memory per capability.

### 4. **Error Handling**

**DO:**
- Handle errors within subgraph
- Return error state from subgraph to parent
- Parent can decide how to handle subgraph failures

**DON'T:**
- Let subgraph errors crash entire system
- Skip error handling because "it's in a subgraph"

**Example:**
```python
def call_rag_subgraph(state: ParentState) -> dict:
    try:
        rag_output = rag_subgraph.invoke(rag_input)
        return {"rag_result": rag_output["final_answer"]}
    except Exception as e:
        log.error(f"RAG subgraph failed: {e}")
        return {"rag_result": None, "rag_error": str(e)}
```

### 5. **Streaming & Observability**

**Enable subgraph streaming:**
```python
for chunk in graph.stream(
    {"user_query": "..."},
    subgraphs=True,  # Include subgraph outputs
    stream_mode="updates",
):
    print(chunk)
```

**Output format:**
- `((), {...})` = Parent graph node
- `(('subgraph_name:thread_id',), {...})` = Subgraph node

**View subgraph state (when interrupted):**
```python
# Only available when subgraph is interrupted
subgraph_state = graph.get_state(config, subgraphs=True).tasks[0].state
```

### 6. **Testing Strategy**

**Unit Tests:**
- Test each subgraph independently
- Mock parent state transformations
- Test subgraph state schemas

**Integration Tests:**
- Test parent graph with real subgraphs
- Test state transformations at boundaries
- Test error propagation

**Example:**
```python
def test_rag_subgraph():
    state = DBRetrievalState(
        user_query="test query",
        # ... minimal required fields
    )
    result = rag_subgraph.invoke(state)
    assert result["final_answer"] is not None
```

### 7. **Migration Strategy**

**Phase 1: DBRetrieval Subgraph (Highest Impact)**
1. Create `DBRetrievalState` schema
2. Create `build_rag_subgraph()` function
3. Create `call_rag_subgraph()` wrapper node
4. Replace `rag` node with `call_rag_subgraph` in parent
5. Test thoroughly
6. Remove old `rag` node

**Phase 2: Image Processing Subgraph**
1. Extract image nodes into subgraph
2. Update DBRetrieval subgraph to invoke it
3. Test

**Phase 3: WebCalcs & DesktopAgent Subgraphs**
1. Create subgraphs for each
2. Update `router_dispatcher` to invoke subgraphs
3. Test

**Phase 4: Cleanup**
1. Remove unused state fields from parent
2. Simplify parent graph structure
3. Update documentation

---

## Implementation Example: DBRetrieval Subgraph

Here's a concrete example of how to implement the DBRetrieval subgraph:

```python
# graph/subgraphs/rag_subgraph.py
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from models.rag_state import RAGState  # Reuse existing, or create DBRetrievalState

def build_rag_subgraph():
    """Build the DBRetrieval subgraph"""
    g = StateGraph(RAGState)  # Or DBRetrievalState if you create it
    
    # Add nodes (same as current)
    g.add_node("rag_plan", node_rag_plan)
    g.add_node("rag_router", node_rag_router)
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("answer", node_answer)
    g.add_node("verify", node_verify)
    g.add_node("correct", node_correct)
    
    # Set entry point
    g.set_entry_point("rag_plan")
    
    # Add edges (simplified - you'll need to adapt routing logic)
    g.add_edge("rag_plan", "rag_router")
    g.add_edge("rag_router", "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "answer")
    g.add_edge("answer", "verify")
    g.add_conditional_edges("verify", _verify_route, {"fix": "retrieve", "ok": "correct"})
    g.add_edge("correct", END)
    
    return g.compile()

# graph/builder.py
def call_rag_subgraph(state: RAGState) -> dict:
    """Wrapper node that invokes RAG subgraph"""
    # Transform parent state to subgraph state (if needed)
    # For now, RAGState works for both, so direct invoke
    rag_output = rag_subgraph.invoke(state)
    
    # Transform subgraph output back to parent state
    return {
        "final_answer": rag_output.get("final_answer"),
        "answer_citations": rag_output.get("answer_citations", []),
        "follow_up_questions": rag_output.get("follow_up_questions", []),
        "follow_up_suggestions": rag_output.get("follow_up_suggestions", []),
        # ... other fields parent needs
    }

# In build_graph():
rag_subgraph = build_rag_subgraph()
g.add_node("rag", call_rag_subgraph)  # Replace old node_rag
```

---

## Benefits Summary

| Benefit | Current State | With Subgraphs |
|---------|---------------|----------------|
| **Modularity** | Flat structure, mixed concerns | Clear capability boundaries |
| **State Management** | One large state for everything | Specialized state per capability |
| **Observability** | All nodes in one stream | Subgraph-aware streaming & debugging |
| **Testability** | Must test entire graph | Test subgraphs independently |
| **Development** | Merge conflicts, shared code | Parallel development, clear interfaces |
| **Maintainability** | Hard to understand structure | Clear architecture matching docs |
| **Scalability** | Adding features affects all | Add features to specific subgraphs |

---

## Next Steps

1. **Review this document** with your team
2. **Start with DBRetrieval subgraph** (biggest impact)
3. **Create `graph/subgraphs/` directory** for subgraph definitions
4. **Implement Phase 1** (DBRetrieval subgraph)
5. **Test thoroughly** before moving to Phase 2
6. **Update Architecture.md** to reflect subgraph structure

---

## References

- [LangGraph Subgraphs Documentation](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- Your Architecture.md: `/Volumes/J/Sid-Master-Repo/Architecture.md`
- Current graph builder: `/Volumes/J/Sid-Master-Repo/Backend/graph/builder.py`
