# KuzuDB Natural Language Integration Plan

## Executive Summary

Integrate KuzuDB graph database with the RAG agent to enable natural language queries that are automatically converted to Cypher queries, executed against the graph database, and returned to the user. The system will intelligently route queries based on intent, with an agent-based verification step before execution.

## Current State Analysis

### ✅ What's Working
- **KuzuDB is fully functional**: Thread-safe singleton pattern, auto-initialization, 26 projects with BIM data loaded
- **LangGraph architecture is mature**: Multi-subgraph system with DBRetrieval, WebCalcs, DesktopAgent subgraphs
- **Text-to-SQL pattern exists**: `/Backend/sid_text2sql/assistant.py` provides a proven blueprint for NL → Query translation
- **LangChain + LangGraph integration**: Already using LangChain components within LangGraph orchestration
- **RAG Router exists**: Intelligent database selection logic in `/Backend/nodes/DBRetrieval/SQLdb/rag_router.py`

### ⚠️ Status Check Needed
The user mentioned this is a new main branch and the previous Kuzu integration code was different. Need to verify:
1. **Kuzu initialization still works** - Auto-loads schema and data in DEBUG_MODE
2. **Database connectivity** - Connection string and credentials are valid
3. **Schema matches data** - BimDB.cypher schema aligns with insertions.cypher data

### ❌ What's Missing
1. **Natural language to Cypher translation** - No component exists to convert user queries to Cypher
2. **Graph query routing logic** - RAG Router doesn't know when to use Kuzu vs. Supabase
3. **Cypher verification agent** - No agent validates generated queries before execution
4. **Result formatting** - Graph results need to be transformed into LangChain Document format for synthesis
5. **Integration with DBRetrieval subgraph** - Kuzu execution must fit into existing RAG pipeline

## User Requirements

1. **Natural Language → Cypher Translation**: User asks "Show me all walls in project X" → System generates Cypher, executes it, returns results
2. **Intelligent Query Routing**: LLM analyzes query intent and decides whether to use Kuzu (graph relationships), Supabase (document semantics), or both
3. **Agent-Based Verification**: A separate agent verifies generated Cypher queries before execution (end users don't see Cypher)
4. **Debug Mode Logging**: In DEBUG_MODE, log generated Cypher queries for developer inspection
5. **Colleague's LangChain Subgraph**: Investigation revealed this refers to existing LangGraph subgraph architecture (already implemented)

## Implementation Plan

### Phase 1: Verify Current Kuzu Integration (PREREQUISITE)

**Objective**: Ensure existing Kuzu setup is functional before building on top of it.

#### Step 1.1: Test Kuzu Database Connection
**File**: `/Backend/nodes/DBRetrieval/KGdb/kuzu_client.py`
- Run a test script to initialize KuzuManager
- Verify database loads from `/Backend/data/kuzu_db`
- Check schema initialization (should auto-load BimDB.cypher in DEBUG_MODE)
- Confirm data is present (insertions.cypher with 26 projects)

**Success Criteria**:
- Database initializes without errors
- Schema tables exist (User, Project, Model, Version, Wall, Floor, etc.)
- Sample query returns data (e.g., `MATCH (p:Project) RETURN count(p)` returns 26)

#### Step 1.2: Validate Schema and Data Consistency
**Files**:
- `/Backend/nodes/DBRetrieval/KGdb/hardcoded-graphs/BimDB.cypher`
- `/Backend/nodes/DBRetrieval/KGdb/hardcoded-graphs/insertions.cypher`

- Run sample queries from `sample_queries.cypher`
- Verify relationships exist (OWNS, CONTAINS_MODEL, HAS_VERSION, REFERENCES_*)
- Check data types match schema (timestamps, booleans, doubles)

**Success Criteria**:
- All sample queries execute successfully
- Relationships return expected traversals
- No type mismatches or missing data

#### Step 1.3: Test API Endpoints (if enabled)
**File**: `/Backend/api_server.py` (lines 2700-2727)
- Test `POST /graph/cypher` endpoint (if DEBUG_MODE enabled)
- Test `GET /graph/schema` endpoint
- Verify thread-safety under concurrent requests

**Success Criteria**:
- Endpoints respond correctly
- No race conditions or deadlocks
- Schema endpoint returns table list

**Action Item**: If any tests fail, add sub-tasks to fix issues before proceeding to Phase 2.

---

### Phase 2: Design Text-to-Cypher Component

**Objective**: Create a robust natural language to Cypher query generator, following the proven `sid_text2sql` pattern.

#### Step 2.1: Create Cypher Generation Prompts
**New File**: `/Backend/prompts/cypher_generator_prompts.py`

**Contents**:
- **CYPHER_SYSTEM_PROMPT**: Instructs LLM on Cypher generation best practices
  - Include full BimDB schema (node types, properties, relationships)
  - Provide 10-15 example queries from `sample_queries.cypher`
  - Emphasize safety: READ-ONLY queries, no CREATE/DELETE/SET operations
  - Include common patterns: traversals, aggregations, filtering, sorting

- **CYPHER_SCHEMA_CONTEXT**: Dynamically fetch current schema via `kuzu_manager.get_schema()`
  - Node tables: User, Project, Model, Version, Wall, Floor, Roof, Beam, Column, etc.
  - Relationship tables: OWNS, CONTAINS_MODEL, HAS_VERSION, REFERENCES_*
  - Property types and constraints

- **CYPHER_EXAMPLES**: Curated examples covering common use cases
  - Project queries: "Find all projects by user X"
  - Element queries: "Show me all structural walls taller than 10ft"
  - Relationship queries: "List all BIM elements in project Y's latest version"
  - Aggregation queries: "Count beams by level for project Z"
  - Material queries: "Find walls with specific material quantities"

**Key Decisions**:
- Use ChatAnthropic with Claude Sonnet 3.5 (best for structured outputs)
- Temperature: 0.1 (deterministic query generation)
- Output format: JSON with fields: `{"cypher_query": "...", "reasoning": "...", "confidence": 0.95}`

#### Step 2.2: Create Cypher Verification Agent
**New File**: `/Backend/nodes/DBRetrieval/KGdb/cypher_verifier.py`

**Purpose**: Validate generated Cypher queries before execution (as per user requirement).

**Verification Checks**:
1. **Safety Validation**:
   - Reject any WRITE operations (CREATE, MERGE, SET, DELETE, DROP)
   - Reject any DETACH operations
   - Ensure query is READ-ONLY

2. **Schema Validation**:
   - Verify node labels exist in schema (e.g., :Project, :Wall)
   - Verify relationship types exist (e.g., -[:CONTAINS_MODEL]->)
   - Check property names are valid

3. **Syntax Validation**:
   - Basic Cypher syntax check (MATCH...RETURN structure)
   - Ensure RETURN clause exists
   - Check for common syntax errors

4. **Complexity Validation**:
   - Limit maximum query depth (prevent expensive traversals)
   - Optional: Set result limit if not specified

**Implementation Approach**:
- Use a separate LLM call with a verification-focused prompt
- Prompt: "You are a Cypher query security auditor. Validate this query..."
- Return: `{"approved": true/false, "issues": [], "corrected_query": "..."}`

**Fallback Strategy**:
- If verifier rejects, try to auto-correct (e.g., add result limit)
- Maximum 2 correction attempts
- If still rejected, fall back to vector search only

#### Step 2.3: Create Text-to-Cypher Assistant
**New File**: `/Backend/nodes/DBRetrieval/KGdb/text_to_cypher_assistant.py`

**Class**: `TextToCypherAssistant` (mirrors `TextToSQLAssistant` from sid_text2sql)

**Key Methods**:
```python
class TextToCypherAssistant:
    def __init__(self, kuzu_manager: KuzuManager, llm: ChatAnthropic):
        self.kuzu_manager = kuzu_manager
        self.llm = llm
        self.schema_cache = None  # Cache schema for 5 minutes

    def generate_cypher(self, user_query: str) -> Dict[str, Any]:
        """Generate Cypher query from natural language."""
        # 1. Get cached schema
        # 2. Build prompt with schema context + examples
        # 3. Call LLM to generate Cypher
        # 4. Parse JSON response
        # 5. Return {"cypher": "...", "reasoning": "...", "confidence": float}

    def verify_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """Verify Cypher query is safe and valid."""
        # 1. Call cypher_verifier agent
        # 2. Return verification result

    def execute_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """Execute verified Cypher query against Kuzu."""
        # 1. Call kuzu_manager.execute(cypher_query)
        # 2. Format results as Documents for RAG pipeline
        # 3. Return {"success": bool, "documents": [...], "row_count": int}

    def query(self, user_query: str) -> Dict[str, Any]:
        """End-to-end: generate, verify, and execute Cypher."""
        # 1. Generate Cypher
        # 2. Verify Cypher (agent-based)
        # 3. Execute if approved
        # 4. Log query in DEBUG_MODE
        # 5. Return formatted results
```

**Error Handling**:
- Wrap all operations in try-except
- Log errors to KUZU_QUERY logger
- Return graceful fallback on failure (vector search only)

**Logging Strategy** (per user requirement):
- In DEBUG_MODE: Log all generated Cypher queries to console and file
- Include: timestamp, user query, generated Cypher, verification result, execution time
- Format: `log_query.info(f"🔍 CYPHER GENERATED: {cypher_query}")`

---

### Phase 3: Integrate with RAG Router

**Objective**: Extend RAG Router to intelligently decide when to query Kuzu, following user's "intelligent routing" requirement.

#### Step 3.1: Extend RAG Router Prompt
**File**: `/Backend/prompts/router_prompts.py`

**Changes**:
- Add "graph_db" as a 5th database option (alongside project_db, code_db, coop_manual, speckle_db)
- Update prompt instructions: "Select graph_db for queries about structural relationships, BIM element hierarchies, project traversals, or when user asks about 'which projects have X' or 'show me all Y in project Z'"

**New Router Output Format**:
```json
{
  "databases": {
    "project_db": true,
    "code_db": false,
    "coop_manual": false,
    "speckle_db": false,
    "graph_db": true  // NEW
  },
  "project_route": "smart",
  "graph_query_intent": "structural_relationships"  // NEW: helps prioritize results
}
```

**Graph Query Intent Types**:
- `"structural_relationships"`: Focus on BIM element relationships (e.g., "walls in project X")
- `"project_hierarchy"`: Focus on User → Project → Model → Version traversal
- `"material_analysis"`: Focus on materialQuantities properties
- `"aggregation"`: Focus on counts, sums, averages across elements

#### Step 3.2: Update RAG Router Node
**File**: `/Backend/nodes/DBRetrieval/SQLdb/rag_router.py`

**Changes**:
- Add `"graph_db": False` to default data_sources dict (line 84)
- Parse new `graph_db` field from router LLM response
- Add graph_query_intent to state
- Log graph_db selection: `log_route.info(f"🕸️ Graph DB enabled: {data_sources['graph_db']}")`

**Heuristic Enhancement** (similar to speckle_db auto-enable on lines 92-99):
```python
# Auto-enable graph_db for structural/relationship queries
graph_keywords = ["project", "model", "version", "wall", "beam", "column", "floor",
                  "roof", "how many", "count", "list all", "show me all"]
if any(k in state.user_query.lower() for k in graph_keywords):
    if not data_sources["graph_db"]:
        log_route.info("🕸️ Auto-enabling graph_db based on structural query keywords")
        data_sources["graph_db"] = True
```

#### Step 3.3: Update DBRetrieval State
**File**: `/Backend/models/db_retrieval_state.py`

**Add New Fields** (after line 32):
```python
# Graph Database (NEW)
graph_db_enabled: bool = False  # Flag indicating graph DB should be queried
cypher_query: Optional[str] = None  # Generated Cypher query
cypher_verification_result: Optional[Dict] = None  # Verification agent result
graph_query_results: List[Document] = field(default_factory=list)  # Results as Documents
graph_query_metadata: Optional[Dict] = None  # Execution metadata (row_count, latency)
```

**Update data_sources default** (line 26-32):
```python
data_sources: Dict[str, bool] = field(
    default_factory=lambda: {
        "project_db": True,
        "code_db": False,
        "coop_manual": False,
        "speckle_db": False,
        "graph_db": False  // NEW
    }
)
```

---

### Phase 4: Create Graph Query Node

**Objective**: Create a new node in the DBRetrieval subgraph that handles Cypher generation, verification, and execution.

#### Step 4.1: Create Graph Query Node
**New File**: `/Backend/nodes/DBRetrieval/KGdb/graph_query_node.py`

**Function**: `node_graph_query(state: DBRetrievalState) -> dict`

**Workflow**:
```python
def node_graph_query(state: DBRetrievalState) -> dict:
    """
    Graph Query Node - Generates, verifies, and executes Cypher queries.
    Only runs if state.data_sources["graph_db"] == True.
    """
    t_start = time.time()
    log_query.info(">>> GRAPH QUERY NODE START")

    # Skip if graph_db not enabled
    if not state.data_sources.get("graph_db", False):
        log_query.info("⏭️ Graph DB not enabled, skipping")
        return {"graph_db_enabled": False}

    try:
        # Step 1: Initialize assistant
        kuzu_manager = get_kuzu_manager()
        assistant = TextToCypherAssistant(kuzu_manager, cypher_llm)

        # Step 2: Generate Cypher query
        log_query.info(f"🤖 Generating Cypher for: '{state.user_query}'")
        generation_result = assistant.generate_cypher(state.user_query)
        cypher_query = generation_result.get("cypher")

        if not cypher_query:
            log_query.warning("⚠️ No Cypher generated, falling back to vector search")
            return {"graph_db_enabled": False}

        # DEBUG MODE: Log generated Cypher
        if DEBUG_MODE:
            log_query.info("=" * 80)
            log_query.info("🔍 GENERATED CYPHER QUERY:")
            log_query.info(cypher_query)
            log_query.info(f"💭 Reasoning: {generation_result.get('reasoning', 'N/A')}")
            log_query.info(f"📊 Confidence: {generation_result.get('confidence', 0.0)}")
            log_query.info("=" * 80)

        # Step 3: Verify Cypher with agent
        log_query.info("🛡️ Verifying Cypher query with agent...")
        verification_result = assistant.verify_cypher(cypher_query)

        if not verification_result.get("approved", False):
            log_query.warning(f"❌ Cypher verification failed: {verification_result.get('issues', [])}")
            # Try corrected query if available
            if verification_result.get("corrected_query"):
                log_query.info("🔧 Using corrected query...")
                cypher_query = verification_result["corrected_query"]
            else:
                return {
                    "graph_db_enabled": False,
                    "cypher_verification_result": verification_result
                }

        log_query.info("✅ Cypher query approved by verification agent")

        # Step 4: Execute Cypher query
        log_query.info("⚡ Executing Cypher query...")
        execution_result = assistant.execute_cypher(cypher_query)

        if not execution_result.get("success", False):
            log_query.error(f"❌ Cypher execution failed: {execution_result.get('error')}")
            return {
                "graph_db_enabled": False,
                "cypher_query": cypher_query,
                "cypher_verification_result": verification_result
            }

        # Step 5: Format results as Documents
        graph_documents = execution_result.get("documents", [])
        row_count = execution_result.get("row_count", 0)

        log_query.info(f"✅ Graph query returned {row_count} results")

        t_elapsed = time.time() - t_start
        log_query.info(f"<<< GRAPH QUERY NODE DONE in {t_elapsed:.2f}s")

        return {
            "graph_db_enabled": True,
            "cypher_query": cypher_query,
            "cypher_verification_result": verification_result,
            "graph_query_results": graph_documents,
            "graph_query_metadata": {
                "row_count": row_count,
                "latency_ms": t_elapsed * 1000,
                "confidence": generation_result.get("confidence", 0.0)
            }
        }

    except Exception as e:
        log_query.error(f"❌ Graph query node failed: {e}")
        import traceback
        traceback.print_exc()
        return {"graph_db_enabled": False}
```

**Key Features**:
- ✅ Conditional execution (only if graph_db enabled)
- ✅ Agent-based verification (per user requirement)
- ✅ DEBUG_MODE logging (per user requirement)
- ✅ Graceful fallback on errors
- ✅ Document-formatted results for synthesis

#### Step 4.2: Update DBRetrieval Subgraph
**File**: `/Backend/graph/subgraphs/db_retrieval_subgraph.py`

**Changes**:

1. **Import new node** (after line 21):
```python
from nodes.DBRetrieval.KGdb.graph_query_node import node_graph_query
```

2. **Add node to graph** (after line 128):
```python
g.add_node("graph_query", node_graph_query)
```

3. **Update routing logic** (after line 141):
```python
# Option 1: Run graph_query in parallel with vector retrieval
# rag_plan_router → [graph_query, retrieve] → merge → grade
g.add_edge("rag_plan_router", "graph_query")
g.add_edge("graph_query", "retrieve")  # Graph results feed into retrieval

# Option 2: Run graph_query before retrieval (sequential)
# rag_plan_router → graph_query → retrieve → grade
# (Choose based on performance testing)
```

**Recommended Flow**:
```
rag_plan_router
    ↓
graph_query (conditional: only if graph_db enabled)
    ↓
retrieve (vector search)
    ↓
grade (grade both graph + vector results)
    ↓
answer (synthesize from both sources)
    ↓
verify
    ↓
correct
```

4. **Update conditional routing function** (modify `_rag_plan_router_to_image_or_retrieve`):
```python
def _rag_plan_router_to_next(state: DBRetrievalState) -> str:
    """Route from rag_plan_router to next node."""
    # Check for image processing first
    if state.images_base64 and state.use_image_similarity:
        return "generate_image_embeddings"

    # Check if graph_db enabled
    if state.data_sources.get("graph_db", False):
        return "graph_query"

    # Default to vector retrieval
    return "retrieve"
```

---

### Phase 5: Merge Graph Results with Vector Results

**Objective**: Combine graph query results with vector search results for unified answer synthesis.

#### Step 5.1: Update Retrieval Node
**File**: `/Backend/nodes/DBRetrieval/SQLdb/retrieve.py`

**Changes** (in `node_retrieve` function):
- Check if graph query was executed: `if state.graph_db_enabled:`
- Prepend graph results to retrieved_docs: `state.graph_query_results + vector_docs`
- Add metadata tag to distinguish sources: `doc.metadata["source_type"] = "graph"` vs `"vector"`

**Code Addition** (before vector retrieval):
```python
# Prepend graph query results if available
initial_docs = []
if state.graph_db_enabled and state.graph_query_results:
    log_query.info(f"📊 Including {len(state.graph_query_results)} graph query results")
    for doc in state.graph_query_results:
        doc.metadata["source_type"] = "graph"
        doc.metadata["cypher_query"] = state.cypher_query  # For citation tracking
    initial_docs = state.graph_query_results

# Perform vector retrieval
vector_docs = hybrid_retriever.get_relevant_documents(...)
for doc in vector_docs:
    doc.metadata["source_type"] = "vector"

# Combine results
all_docs = initial_docs + vector_docs
```

#### Step 5.2: Update Grading Node
**File**: `/Backend/nodes/DBRetrieval/SQLdb/grade.py`

**Changes**:
- Recognize graph-sourced documents: `if doc.metadata.get("source_type") == "graph"`
- Apply different grading strategy:
  - Graph results: Grade as "relevant" by default (user explicitly queried graph relationships)
  - Vector results: Use existing LLM-based relevance grading
- Preserve graph results through grading pipeline

**Code Addition**:
```python
graded_docs = []
for doc in state.retrieved_docs:
    if doc.metadata.get("source_type") == "graph":
        # Graph results are pre-filtered by Cypher query, treat as relevant
        graded_docs.append(doc)
    else:
        # Grade vector search results as before
        grade_result = grader.invoke(...)
        if grade_result == "relevant":
            graded_docs.append(doc)
```

#### Step 5.3: Update Answer Synthesis
**File**: `/Backend/nodes/DBRetrieval/SQLdb/answer.py` and `/Backend/synthesis/synthesizer.py`

**Changes**:
- Group documents by source_type: graph vs. vector
- Prioritize graph results in answer (they match user's structural query intent)
- Include Cypher query in citations for graph results

**Synthesizer Enhancement**:
```python
def synthesize(...):
    # Separate graph and vector documents
    graph_docs = [d for d in graded_docs if d.metadata.get("source_type") == "graph"]
    vector_docs = [d for d in graded_docs if d.metadata.get("source_type") == "vector"]

    # Build answer with graph results prioritized
    if graph_docs:
        answer_parts.append("**Graph Database Results:**")
        # Synthesize graph results first

    if vector_docs:
        answer_parts.append("**Document Search Results:**")
        # Synthesize vector results second

    # Combine into final answer
```

**Citation Format for Graph Results**:
```python
{
    "source": "graph_database",
    "cypher_query": state.cypher_query,
    "row_count": state.graph_query_metadata["row_count"],
    "snippet": doc.page_content[:200],
    "confidence": state.graph_query_metadata["confidence"]
}
```

---

### Phase 6: End-to-End Testing and Refinement

**Objective**: Validate the complete integration works correctly and refine based on real-world usage.

#### Step 6.1: Create Test Suite
**New File**: `/Backend/tests/test_kuzu_integration.py`

**Test Cases**:
1. **Test 1: Simple Project Query**
   - Input: "How many projects are in the database?"
   - Expected: Cypher generated, verified, executed, returns count

2. **Test 2: Structural Element Query**
   - Input: "Show me all walls in project 25-01-161"
   - Expected: Graph DB routed, Cypher with project filter, returns wall list

3. **Test 3: Relationship Traversal**
   - Input: "List all BIM elements in the latest version of the Westlake project"
   - Expected: Multi-hop Cypher query (Project → Model → Version → Elements)

4. **Test 4: Hybrid Query (Graph + Vector)**
   - Input: "What are the specifications for structural beams in project X?"
   - Expected: Both graph_db (beam list) and vector search (specs docs) enabled

5. **Test 5: Fallback on Verification Failure**
   - Input: Inject malicious query that tries to DELETE nodes
   - Expected: Verification agent rejects, falls back to vector search only

6. **Test 6: Debug Mode Logging**
   - Enable DEBUG_MODE
   - Run any query
   - Verify Cypher query logged to console and file

#### Step 6.2: Performance Benchmarking
**Metrics to Track**:
- Cypher generation latency (target: <1s)
- Verification latency (target: <500ms)
- Execution latency (target: <500ms for typical queries)
- End-to-end latency (graph + vector pipeline)
- Result quality (human evaluation)

#### Step 6.3: Refinement Based on Results
**Potential Adjustments**:
1. **If Cypher generation is inaccurate**:
   - Add more examples to CYPHER_SYSTEM_PROMPT
   - Use few-shot learning with user-approved queries
   - Implement query correction loop (regenerate if execution fails)

2. **If verification is too strict**:
   - Relax safety constraints (but keep WRITE operations blocked)
   - Allow more complex queries (increase depth limit)

3. **If graph results are low-quality**:
   - Improve result formatting (convert rows to natural language)
   - Add context from related nodes (e.g., include project name with walls)

4. **If latency is too high**:
   - Cache schema more aggressively (increase TTL)
   - Parallelize graph query with vector retrieval (use ThreadPoolExecutor)
   - Add result limits to Cypher queries by default

---

## Critical Files to Modify

### New Files to Create:
1. `/Backend/prompts/cypher_generator_prompts.py` - Cypher generation prompts
2. `/Backend/nodes/DBRetrieval/KGdb/cypher_verifier.py` - Verification agent
3. `/Backend/nodes/DBRetrieval/KGdb/text_to_cypher_assistant.py` - Main assistant class
4. `/Backend/nodes/DBRetrieval/KGdb/graph_query_node.py` - LangGraph node
5. `/Backend/tests/test_kuzu_integration.py` - Test suite

### Existing Files to Modify:
1. `/Backend/prompts/router_prompts.py` - Add graph_db routing logic
2. `/Backend/nodes/DBRetrieval/SQLdb/rag_router.py` - Parse graph_db selection
3. `/Backend/models/db_retrieval_state.py` - Add graph query fields
4. `/Backend/graph/subgraphs/db_retrieval_subgraph.py` - Add graph_query node
5. `/Backend/nodes/DBRetrieval/SQLdb/retrieve.py` - Merge graph + vector results
6. `/Backend/nodes/DBRetrieval/SQLdb/grade.py` - Grade graph results differently
7. `/Backend/nodes/DBRetrieval/SQLdb/answer.py` - Prioritize graph results in synthesis
8. `/Backend/synthesis/synthesizer.py` - Format citations for graph results
9. `/Backend/config/llm_instances.py` - Add cypher_llm instance (if needed)

---

## Verification Plan

### How to Test End-to-End

#### Step 1: Start Backend Server
```bash
cd /home/proffessorq/Work/Sid-Master-Repo/Backend
export DEBUG_MODE=true  # Enable debug logging
python api_server.py
```

#### Step 2: Send Test Query via API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many walls are in project 25-01-161?",
    "session_id": "test-session",
    "user_identifier": "test-user"
  }'
```

#### Step 3: Verify Response Contains Graph Results
**Expected Response Structure**:
```json
{
  "reply": "According to the graph database, project 25-01-161 contains 42 walls...",
  "session_id": "test-session",
  "citations": [
    {
      "source": "graph_database",
      "cypher_query": "MATCH (p:Project {name: '25-01-161'})-[...]-(w:Wall) RETURN count(w)",
      "row_count": 1,
      "confidence": 0.95
    }
  ],
  "route": "rag",
  "latency_ms": 1250
}
```

#### Step 4: Check Logs for Cypher Query (DEBUG_MODE)
**Look for Log Output**:
```
[KUZU_QUERY] 🔍 GENERATED CYPHER QUERY:
================================================================================
MATCH (p:Project {name: '25-01-161'})-[:CONTAINS_MODEL]->(m:Model)
      -[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall)
RETURN count(w) AS wall_count
================================================================================
[KUZU_QUERY] 💭 Reasoning: User is asking for a count of walls in a specific project...
[KUZU_QUERY] 📊 Confidence: 0.95
[KUZU_QUERY] 🛡️ Verifying Cypher query with agent...
[KUZU_QUERY] ✅ Cypher query approved by verification agent
[KUZU_QUERY] ⚡ Executing Cypher query...
[KUZU_QUERY] ✅ Graph query returned 1 results
```

#### Step 5: Test Hybrid Query (Graph + Vector)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the fire safety requirements for the beams in project X, and show me all beams in the database?",
    "session_id": "test-session-2"
  }'
```

**Expected Behavior**:
- RAG Router enables both `graph_db: true` (for beam list) and `project_db: true` (for fire safety docs)
- Graph query executes: Returns list of beams
- Vector search executes: Returns fire safety documents
- Answer synthesis combines both: "Here are all beams in the database: [graph results]. Fire safety requirements: [vector results]"

#### Step 6: Test Verification Rejection
**Inject malicious query** (in test environment):
```python
# In test_kuzu_integration.py
def test_verification_rejects_write_operations():
    assistant = TextToCypherAssistant(kuzu_manager, llm)
    malicious_query = "MATCH (p:Project) DELETE p"

    verification_result = assistant.verify_cypher(malicious_query)

    assert verification_result["approved"] == False
    assert "WRITE operation detected" in verification_result["issues"]
```

---

## Risks and Mitigations

### Risk 1: Cypher Generation Inaccuracy
**Impact**: User gets wrong results or query fails
**Mitigation**:
- Include 15+ high-quality examples in prompt
- Implement query correction loop (retry on execution error)
- Log all queries in DEBUG_MODE for human review and improvement

### Risk 2: Verification Agent Too Strict
**Impact**: Valid queries rejected, frustrating UX
**Mitigation**:
- Start permissive, tighten gradually based on abuse
- Provide detailed rejection reasons for debugging
- Allow manual override in DEBUG_MODE

### Risk 3: Performance Degradation
**Impact**: Adding graph query increases latency
**Mitigation**:
- Run graph query in parallel with vector retrieval (ThreadPoolExecutor)
- Cache schema aggressively (5-minute TTL)
- Set default result limits on Cypher queries (e.g., LIMIT 100)

### Risk 4: Schema Changes Break Queries
**Impact**: Database schema evolves, prompts become outdated
**Mitigation**:
- Dynamically fetch schema via `kuzu_manager.get_schema()`
- Include schema version in prompts
- Set up schema change detection (alert if tables/rels change)

### Risk 5: Kuzu Database Not Functional
**Impact**: Phase 1 verification fails, entire plan blocked
**Mitigation**:
- Run Phase 1 verification FIRST before any implementation
- Document all issues found and create sub-tasks to fix
- Have fallback plan: Use only vector search until Kuzu fixed

---

## Success Criteria

### Functional Requirements:
- ✅ User can ask natural language questions about BIM structure
- ✅ System generates valid Cypher queries automatically
- ✅ Verification agent approves safe queries, rejects unsafe ones
- ✅ Graph results are merged with vector search results
- ✅ Answer synthesis includes graph-sourced data with citations
- ✅ DEBUG_MODE logs all Cypher queries for developer inspection

### Non-Functional Requirements:
- ✅ End-to-end latency < 3 seconds (P95)
- ✅ Cypher generation accuracy > 90% (human evaluation)
- ✅ Zero WRITE operations executed in production
- ✅ Graceful fallback when graph query fails
- ✅ Logs provide clear debugging trail

### User Experience:
- ✅ End users never see Cypher (agent handles verification internally)
- ✅ Responses feel natural and accurate
- ✅ Citations distinguish graph vs. document sources
- ✅ Hybrid queries (graph + vector) work seamlessly

---

## Timeline Estimate

**Phase 1 (Verification)**: 2-4 hours
- Test current Kuzu setup
- Fix any issues found

**Phase 2 (Text-to-Cypher Component)**: 6-8 hours
- Create prompts (2 hours)
- Implement verifier agent (2 hours)
- Implement assistant class (3 hours)
- Testing (1 hour)

**Phase 3 (RAG Router Integration)**: 3-4 hours
- Update router prompt (1 hour)
- Modify router node (1 hour)
- Update state model (1 hour)

**Phase 4 (Graph Query Node)**: 4-6 hours
- Implement node function (2 hours)
- Update subgraph (1 hour)
- Integration testing (2 hours)

**Phase 5 (Result Merging)**: 4-5 hours
- Update retrieval node (1 hour)
- Update grading node (1 hour)
- Update synthesis (2 hours)

**Phase 6 (E2E Testing)**: 4-6 hours
- Create test suite (2 hours)
- Performance benchmarking (1 hour)
- Refinement (2 hours)

**Total Estimate**: 23-33 hours

---

## Next Steps

1. **Get Plan Approval**: Review this plan with the user, address any questions
2. **Run Phase 1 Verification**: Test Kuzu database immediately, document results
3. **Create Implementation Branch**: `git checkout -b feature/kuzu-nl-integration`
4. **Implement Phase by Phase**: Follow plan sequentially, commit after each phase
5. **Continuous Testing**: Run test suite after each phase to catch issues early
6. **Iterate Based on Feedback**: Refine approach based on test results and user feedback

---

**Plan Status**: Ready for approval ✅
**Last Updated**: 2026-01-14
**Plan Author**: Claude Sonnet 4.5