# Log Source Map - Where Each Log Comes From

## Log Flow Pipeline

### 1. **Strategic Planning Log** 🎯
**Source:** `localagent/agents/search_orchestrator.py` line 5331
- **File:** `search_orchestrator.py`
- **Function:** `SearchOrchestrator.execute()`
- **When:** Right after getting strategic planning from TeamOrchestrator
- **Content:** Intent classification, data sources, strategy, reasoning
- **Code:**
```python
trace.thinking_log.append(f"## 🎯 Strategic Planning\n\n**What I'm analyzing:** ...")
```

### 2. **Starting RAG Search Log** 📚
**Source:** `localagent/agents/search_orchestrator.py` line 5360
- **File:** `search_orchestrator.py`
- **Function:** `SearchOrchestrator.execute()` → RAG execution block
- **When:** Before calling `run_agentic_rag()`
- **Content:** What RAG is doing, query, data sources, how it works
- **Code:**
```python
trace.thinking_log.append(f"## 📚 Starting RAG Search\n\n**What I'm doing:** ...")
```

### 3. **RAG Search Complete Log** ✅
**Source:** `localagent/agents/search_orchestrator.py` line 5381
- **File:** `search_orchestrator.py`
- **Function:** `SearchOrchestrator.execute()` → After RAG completes
- **When:** After `run_agentic_rag()` returns
- **Content:** Results summary, citations count, what happened
- **Code:**
```python
trace.thinking_log.append(f"## ✅ RAG Search Complete\n\n**Results:** ...")
```

### 4. **Planning Information Log** (from backend)
**Source:** `backend/main.py` line 300-318
- **File:** `main.py`
- **Function:** `chat()` endpoint
- **When:** After TeamOrchestrator returns result
- **Content:** Strategic planning details formatted for frontend
- **Code:**
```python
planning_text = f"## 🎯 Strategic Planning\n\n..."
thinking_logs.insert(0, {...})
```

### 5. **Execution Steps Logs** (from backend)
**Source:** `backend/main.py` line 268-298
- **File:** `main.py`
- **Function:** `chat()` endpoint → Processing trace.steps
- **When:** For each execution step in the trace
- **Content:** Tool name, what it's doing, status
- **Code:**
```python
for step in trace.steps:
    thinking_logs.append({...})
```

## Decision Pipeline Flow

### Step 1: User Query → Backend
**File:** `backend/main.py` line 225-254
- User sends message via `/chat` endpoint
- Backend receives `ChatRequest` with message, session_id, data_sources

### Step 2: TeamOrchestrator Strategic Planning
**File:** `localagent/agents/team_orchestrator.py` line 49-164
- **Function:** `plan_execution(user_query)`
- **Decision:** Uses LLM (gpt-4o-mini) to determine:
  - **Intent:** project_search, design_guidance, process_knowledge, etc.
  - **Data Sources:** supabase_metadata, rag_documents, rag_codes, etc.
  - **Strategy:** metadata_first, document_first, code_first, etc.
- **Output:** Planning dict with intent, data_sources, strategy, reasoning

### Step 3: TeamOrchestrator Fast Routing
**File:** `localagent/agents/team_orchestrator.py` line 166-209
- **Function:** `route_task(user_query)`
- **Decision:** Uses LLM (gpt-4o-mini) to determine which specialized agent:
  - "search" → SearchOrchestrator
  - "document" → DocumentOrchestrator (future)
  - "analysis" → AnalysisOrchestrator (future)
- **Output:** Routing dict with agent_type, confidence, reasoning

### Step 4: Delegate to Specialized Agent
**File:** `localagent/agents/team_orchestrator.py` line 211-271
- **Function:** `execute(task, context)`
- **Action:** Calls `specialized_agent.execute(task, context_with_planning)`
- Passes planning and routing info in context

### Step 5: SearchOrchestrator Execution
**File:** `localagent/agents/search_orchestrator.py` line 5299-5542
- **Function:** `SearchOrchestrator.execute(task, context)`
- **Decisions:**
  1. Extract strategic planning from context
  2. Convert data_sources list to RAG format dict
  3. Determine if RAG is needed (always True for search)
  4. Determine if metadata search is needed
  5. Execute RAG (embeds query, searches Supabase vector stores)
  6. Execute metadata search (if needed)
  7. Combine results

### Step 6: RAG System Execution
**File:** `localagent/agents/search_orchestrator.py` line 4804-4976
- **Function:** `run_agentic_rag(question, session_id, data_sources)` 
- **Note:** This is a COPY of the RAG code from `backend/RAG/rag.py` - the original `backend/RAG/rag.py` is NOT used anymore
- **Process:**
  1. Query rewriting and expansion
  2. Vector search in Supabase (smart_chunks, page_chunks, code_chunks, coop_chunks)
  3. Document retrieval and grading
  4. Answer synthesis using LLM
  5. Citation extraction
- **Called from:** `SearchOrchestrator.execute()` at line 5372

### Step 7: Backend Formats Response
**File:** `backend/main.py` line 256-427
- **Function:** `chat()` endpoint
- **Actions:**
  1. Extract thinking_logs from trace
  2. Extract execution steps from trace
  3. Format planning information
  4. Extract final answer from results
  5. Return JSON response with reply, thinking_logs, planning, routing

### Step 8: Frontend Receives and Displays
**File:** `Frontend/components/SmartChatPanel.vue` line 405-450
- **Function:** `handleSend()`
- **Actions:**
  1. Call `sendChatMessage()` or `sendChatMessageStream()`
  2. Receive response with thinking_logs
  3. Emit each log to AgentLogsPanel via `emitAgentLog()`
  4. Display answer in chat

**File:** `Frontend/pages/index.vue` line 287-293
- **Function:** `handleAgentLog(log)`
- **Actions:**
  1. Add log to `agentLogs` array
  2. Open logs panel if closed: `logsPanelOpen.value = true`

## Panel Visibility Control

**File:** `Frontend/pages/index.vue` line 186, 292-293
- **Variable:** `logsPanelOpen` (ref)
- **Auto-open:** When first log is received
- **Auto-close:** Currently NEVER (stays open ~40 seconds)
- **Manual close:** User clicks X button

## Key Decision Points

1. **Intent Classification** → Determines what type of query
   - Location: `team_orchestrator.py:plan_execution()`
   - Uses: LLM (gpt-4o-mini) with JSON response format

2. **Agent Routing** → Determines which specialized agent
   - Location: `team_orchestrator.py:route_task()`
   - Uses: LLM (gpt-4o-mini) with JSON response format

3. **Data Source Selection** → Determines which databases to query
   - Location: `team_orchestrator.py:plan_execution()`
   - Based on: Intent classification

4. **Strategy Selection** → Determines execution order
   - Location: `team_orchestrator.py:plan_execution()`
   - Examples: metadata_first, document_first, code_first

5. **RAG vs Metadata** → Determines search approach
   - Location: `search_orchestrator.py:execute()`
   - Based on: Strategic planning data_sources

