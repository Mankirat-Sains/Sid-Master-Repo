# Decision Pipeline - Complete Flow

## Overview
This document explains the complete decision-making pipeline from user query to final answer.

## Architecture

```
User Query
    ↓
Backend API (/chat)
    ↓
TeamOrchestrator (Strategic Planning + Fast Routing)
    ↓
SearchOrchestrator (Tactical Execution)
    ↓
RAG System (Embedding + Vector Search + Answer Generation)
    ↓
Response to User
```

---

## Step-by-Step Pipeline

### Step 1: User Query → Backend API
**File:** `backend/main.py` line 225-254
- **Endpoint:** `POST /chat`
- **Input:** `ChatRequest` with:
  - `message`: User's query string
  - `session_id`: Session identifier
  - `data_sources`: Which databases to search (optional)
  - `images_base64`: Optional images

**What happens:**
- Backend receives the request
- Prepares context for TeamOrchestrator
- Calls `team_orchestrator.execute(task, context)`

---

### Step 2: TeamOrchestrator - Strategic Planning
**File:** `localagent/agents/team_orchestrator.py` line 49-164
**Function:** `plan_execution(user_query)`

**Decision Process:**
1. **Uses LLM (gpt-4o-mini)** with JSON response format
2. **Analyzes query** to determine:
   - **Intent:** What type of query is this?
     - `project_search`: Finding specific projects
     - `design_guidance`: How to design something
     - `process_knowledge`: Company-specific processes
     - `technical_question`: General engineering questions
   
   - **Data Sources:** Which systems to query?
     - `supabase_metadata`: Project metadata (dimensions, types, materials)
     - `rag_documents`: Project documents, technical drawings
     - `rag_codes`: Building codes, standards
     - `rag_internal_docs`: Company processes, training manuals
     - `graphql_speckle`: 3D models, relationships
     - `calculation_tools`: Structural analysis, section properties
   
   - **Strategy:** How to execute?
     - `metadata_first`: Query structured metadata first, then documents
     - `document_first`: Search documents first, extract metadata
     - `code_first`: Search codes first, extract parameters, then calculate
     - `process_only`: Search internal docs only
     - `hybrid`: Multiple sources in parallel

**Output:** Planning dict with:
```python
{
  "intent": "project_search",
  "data_sources": ["supabase_metadata", "rag_documents"],
  "strategy": "metadata_first",
  "reasoning": "Why this approach",
  "expected_steps": ["step1", "step2", ...]
}
```

**Code Location:** `team_orchestrator.py:98-141` (LLM call)

---

### Step 3: TeamOrchestrator - Fast Routing
**File:** `localagent/agents/team_orchestrator.py` line 166-209
**Function:** `route_task(user_query)`

**Decision Process:**
1. **Uses LLM (gpt-4o-mini)** with minimal prompt for speed
2. **Classifies query** into agent types:
   - `"search"` → SearchOrchestrator
   - `"document"` → DocumentOrchestrator (future)
   - `"analysis"` → AnalysisOrchestrator (future)
   - `"general"` → General agent

**Output:** Routing dict with:
```python
{
  "agent_type": "search",
  "confidence": 0.9,
  "reasoning": "Contains search keywords"
}
```

**Code Location:** `team_orchestrator.py:184-204` (LLM call)

---

### Step 4: Delegate to Specialized Agent
**File:** `localagent/agents/team_orchestrator.py` line 211-271
**Function:** `execute(task, context)`

**What happens:**
1. Combines planning and routing info into `context_with_planning`
2. Gets specialized agent: `specialized_agent = self.specialized_agents.get(agent_type)`
3. Calls: `result = specialized_agent.execute(task, context_with_planning)`
4. Adds planning/routing info to result

**Code Location:** `team_orchestrator.py:238-263`

---

### Step 5: SearchOrchestrator - Tactical Execution
**File:** `localagent/agents/search_orchestrator.py` line 5299-5542
**Function:** `SearchOrchestrator.execute(task, context)`

**Decision Process:**

1. **Extract Strategic Planning** from context
   - Gets `intent`, `data_sources`, `strategy` from `context["planning"]`
   - **Code:** `search_orchestrator.py:5325-5328`

2. **Convert Data Sources** to RAG format
   - Strategic planning uses: `["rag_documents", "rag_codes", "supabase_metadata"]`
   - RAG expects: `{"project_db": True, "code_db": False, "coop_manual": False}`
   - **Code:** `search_orchestrator.py:5336-5346`

3. **Determine What to Execute**
   - `needs_rag = True` (always for search - embeds query and searches Supabase)
   - `needs_metadata = any("supabase" in src or "metadata" in src for src in data_sources_list)`
   - **Code:** `search_orchestrator.py:5348-5352`

4. **Execute RAG** (if needed)
   - Calls `run_agentic_rag()` - **THIS IS THE COPY IN search_orchestrator.py**
   - **Code:** `search_orchestrator.py:5372-5377`

5. **Execute Metadata Search** (if needed)
   - Uses LangGraph workflow or tools directly
   - **Code:** `search_orchestrator.py:5394-5447`

6. **Combine Results**
   - Merges RAG answer and metadata results
   - **Code:** `search_orchestrator.py:5454-5482`

**Key Decision Point:** 
- The `run_agentic_rag()` function called here is **defined in the same file** (`search_orchestrator.py:4804`), NOT imported from `backend/RAG/rag.py`

---

### Step 6: RAG System Execution
**File:** `localagent/agents/search_orchestrator.py` line 4804-4976
**Function:** `run_agentic_rag(question, session_id, data_sources)`

**⚠️ IMPORTANT:** This is a **COPY** of the RAG code from `backend/RAG/rag.py`. The original `backend/RAG/rag.py` is **NOT used** by SearchOrchestrator.

**Process:**

1. **Build LangGraph Workflow**
   - Creates graph with nodes: `plan`, `retrieve`, `grade`, `synthesize`
   - **Code:** `search_orchestrator.py:4823` → calls `build_graph()`

2. **Query Rewriting**
   - Uses `intelligent_query_rewriter()` to expand/rewrite query
   - Extracts project filters
   - **Code:** `search_orchestrator.py:4872-4883`

3. **Vector Search in Supabase**
   - Embeds query using `OpenAIEmbeddings`
   - Searches vector stores:
     - `vs_smart` → `smart_chunks` table
     - `vs_large` → `page_chunks` table
     - `vs_code` → `code_chunks` table (if code_db enabled)
     - `vs_coop` → `coop_chunks` table (if coop_manual enabled)
   - **Code:** `search_orchestrator.py:node_retrieve()` function

4. **Document Retrieval & Grading**
   - Retrieves top-k chunks from vector stores
   - Grades relevance using LLM
   - **Code:** `search_orchestrator.py:node_grade()` function

5. **Answer Synthesis**
   - Uses LLM to generate answer from retrieved chunks
   - Includes citations
   - **Code:** `search_orchestrator.py:synthesize()` function (line 3006)

6. **Return Results**
   - Returns dict with `answer`, `citations`, `support`, etc.
   - **Code:** `search_orchestrator.py:4907-4976`

**Called from:** `SearchOrchestrator.execute()` at line 5372

---

### Step 7: Backend Formats Response
**File:** `backend/main.py` line 256-427
**Function:** `chat()` endpoint

**What happens:**

1. **Extract Thinking Logs** from trace
   - Gets `trace.thinking_log` (list of strings)
   - Converts to AgentLog format
   - **Code:** `main.py:260-266`

2. **Extract Execution Steps** from trace
   - Gets `trace.steps` (list of ExecutionStep objects)
   - Formats each step as a log entry
   - **Code:** `main.py:269-298`

3. **Format Planning Information**
   - Creates formatted planning log
   - Inserts at beginning of thinking_logs
   - **Code:** `main.py:300-318`

4. **Extract Final Answer**
   - Gets answer from `result["results"]["answer"]`
   - Handles various result formats
   - **Code:** `main.py:320-406`

5. **Return JSON Response**
   ```python
   {
     "reply": "Full answer text",
     "thinking_logs": [...],
     "planning": {...},
     "routing": {...},
     "citations": 50,
     ...
   }
   ```
   - **Code:** `main.py:417-427`

---

### Step 8: Frontend Receives and Displays
**File:** `Frontend/components/SmartChatPanel.vue` line 405-470
**Function:** `handleSend()`

**What happens:**

1. **Call Backend** (streaming or non-streaming)
   - Uses `sendChatMessageStream()` for streaming
   - Or `sendChatMessage()` for non-streaming
   - **Code:** `SmartChatPanel.vue:421-446`

2. **Stream Logs** (if streaming)
   - Receives logs via `onLog` callback
   - Emits each log: `emitAgentLog(log)`
   - **Code:** `SmartChatPanel.vue:427-434`

3. **Stream Answer** (if streaming)
   - Receives chunks via `onChunk` callback
   - Updates message content incrementally
   - **Code:** `SmartChatPanel.vue:436-445`

4. **Display Final Answer**
   - Adds message to `messages` array
   - Shows in chat panel
   - **Code:** `SmartChatPanel.vue:443-450`

**File:** `Frontend/pages/index.vue` line 287-310
**Function:** `handleAgentLog(log)`

**What happens:**
1. Adds log to `agentLogs` array
2. Opens logs panel if closed
3. Sets `isProcessing = true`
4. Starts/resets auto-close timer (10 seconds)

---

## Key Decision Points Summary

| Decision | Location | Method | Output |
|----------|----------|--------|--------|
| **Intent Classification** | `team_orchestrator.py:49-164` | LLM (gpt-4o-mini) | `intent` (project_search, design_guidance, etc.) |
| **Data Source Selection** | `team_orchestrator.py:49-164` | LLM (gpt-4o-mini) | `data_sources` list |
| **Strategy Selection** | `team_orchestrator.py:49-164` | LLM (gpt-4o-mini) | `strategy` (metadata_first, document_first, etc.) |
| **Agent Routing** | `team_orchestrator.py:166-209` | LLM (gpt-4o-mini) | `agent_type` (search, document, etc.) |
| **RAG vs Metadata** | `search_orchestrator.py:5348-5352` | Conditional logic | `needs_rag`, `needs_metadata` flags |
| **Query Rewriting** | `search_orchestrator.py:4872` | `intelligent_query_rewriter()` | Rewritten query + filters |
| **Vector Search** | `search_orchestrator.py:node_retrieve()` | Supabase vector stores | Retrieved document chunks |
| **Answer Synthesis** | `search_orchestrator.py:synthesize()` | LLM (gpt-4o-mini) | Final answer + citations |

---

## Important Notes

1. **RAG Code Location:** The RAG system used by SearchOrchestrator is **in `search_orchestrator.py`** (line 4804), NOT in `backend/RAG/rag.py`. The original RAG file is not imported or used.

2. **Two-Level Planning:**
   - **Strategic** (TeamOrchestrator): WHAT to do, which data sources, which strategy
   - **Tactical** (SearchOrchestrator): HOW to execute, detailed steps

3. **Streaming:** The system supports streaming via `/chat/stream` endpoint, which streams both logs and answer chunks as they're generated.

4. **Logs vs Answer:**
   - **Logs:** Show the thinking/process (what tools, what documents searched, etc.)
   - **Answer:** Shows only the final answer (no breakdown of how it was found)




