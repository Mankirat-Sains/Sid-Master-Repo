# Complete Query Flow Trace: "Find me a project with a sandwich wall"

This document traces the **exact** flow of decisions, logs, and answer generation for the query: **"Find me a project with a sandwich wall"**

---

## 🎯 Step 1: User Query → Backend API

**Location:** `backend/main.py` line 225-254  
**Endpoint:** `POST /chat`

**What happens:**
1. Frontend sends HTTP POST request to `/chat` endpoint
2. Backend receives:
   ```json
   {
     "message": "Find me a project with a sandwich wall",
     "session_id": "session_123",
     "data_sources": null  // Optional
   }
   ```
3. Backend calls: `team_orchestrator.execute(task="Find me a project with a sandwich wall", context={...})`

**Logs created:** None yet (backend just receives request)

---

## 🧠 Step 2: TeamOrchestrator - Strategic Planning

**Location:** `localagent/agents/team_orchestrator.py` line 49-164  
**Function:** `plan_execution(user_query)`

### Decision Process:

1. **LLM Call** (gpt-4o-mini) at line 98-141
   - **Prompt:** System prompt asking to classify intent, select data sources, choose strategy
   - **User query:** "Find me a project with a sandwich wall"
   - **LLM analyzes:**
     - Intent: `project_search` (user wants to find projects)
     - Data sources: `["supabase_metadata", "rag_documents"]` (needs metadata + document search)
     - Strategy: `metadata_first` (query metadata first, then search documents)
     - Reasoning: "User wants to find projects with specific feature (sandwich wall) - will query metadata then search documents"

2. **Output:**
   ```python
   {
     "intent": "project_search",
     "data_sources": ["supabase_metadata", "rag_documents"],
     "strategy": "metadata_first",
     "reasoning": "User wants to find projects with specific feature...",
     "expected_steps": ["Extract search criteria", "Query metadata", "Search documents", "Return results"],
     "planning_intelligence": {
       "intent_classification": "project_search",
       "data_source_count": 2,
       "strategy": "metadata_first",
       "confidence": 0.9
     }
   }
   ```

**Logs created:** None yet (planning happens internally)

---

## 🚀 Step 3: TeamOrchestrator - Fast Routing

**Location:** `localagent/agents/team_orchestrator.py` line 166-209  
**Function:** `route_task(user_query)`

### Decision Process:

1. **LLM Call** (gpt-4o-mini) at line 184-204
   - **Prompt:** Minimal prompt asking which agent type
   - **User query:** "Find me a project with a sandwich wall"
   - **LLM decides:** `"search"` (this is a search query)

2. **Output:**
   ```python
   {
     "agent_type": "search",
     "confidence": 0.95,
     "reasoning": "Contains search keywords: 'find', 'project'"
   }
   ```

**Logs created:** None yet (routing happens internally)

---

## 📤 Step 4: Delegate to SearchOrchestrator

**Location:** `localagent/agents/team_orchestrator.py` line 211-271  
**Function:** `execute(task, context)`

**What happens:**
1. Gets `SearchOrchestrator` from `self.specialized_agents["search"]`
2. Combines planning + routing into context:
   ```python
   context_with_planning = {
     "planning": {
       "intent": "project_search",
       "data_sources": ["supabase_metadata", "rag_documents"],
       "strategy": "metadata_first",
       ...
     },
     "routing": {
       "agent_type": "search",
       ...
     }
   }
   ```
3. Calls: `result = search_orchestrator.execute(task, context_with_planning)`

**Logs created:** None yet (delegation happens internally)

---

## 🔍 Step 5: SearchOrchestrator - Extract Planning & Convert Data Sources

**Location:** `localagent/agents/search_orchestrator.py` line 5299-5542  
**Function:** `SearchOrchestrator.execute(task, context)`

### Decision Process:

1. **Extract Strategic Planning** (line 5325-5328)
   - Gets `intent = "project_search"`
   - Gets `data_sources = ["supabase_metadata", "rag_documents"]`
   - Gets `strategy = "metadata_first"`

2. **Convert Data Sources** (line 5336-5346)
   - Strategic planning uses: `["rag_documents", "supabase_metadata"]`
   - Converts to RAG format:
     ```python
     data_sources_config = {
       "project_db": True,   # rag_documents → project_db
       "code_db": False,
       "coop_manual": False
     }
     ```

3. **Determine What to Execute** (line 5348-5352)
   - `needs_rag = True` (always for search - embeds query and searches Supabase)
   - `needs_metadata = True` (because "supabase_metadata" in data_sources)

4. **Create Strategic Planning Log** (line 5331)
   - **LOG CREATED:** 
     ```markdown
     ## 🎯 Strategic Planning
     
     **What I'm analyzing:** Your query to determine the best approach.
     
     **Intent Classification:** project_search
     - This tells me what type of query you're asking (project search, design guidance, etc.)
     
     **Data Sources Selected:** supabase_metadata, rag_documents
     - These are the systems I'll query to find your answer
     
     **Execution Strategy:** metadata_first
     - This determines the order and approach I'll use to get the information
     
     **My reasoning:** Based on your query, I've determined this is the most efficient way to find what you're looking for.
     ```
   - **Added to:** `trace.thinking_log.append(...)`

5. **Execute RAG** (line 5360-5377)
   - **LOG CREATED:** 
     ```markdown
     ## 📚 Starting RAG Search
     
     **What I'm doing:** Embedding your query and searching Supabase vector stores (smart_chunks, page_chunks, code_chunks, coop_chunks) to find relevant documents.
     
     **Your query:** 'Find me a project with a sandwich wall'
     
     **Searching in:**
     - Project documents: Yes
     - Code references: No
     - Coop manual: No
     
     **How it works:**
     1. Convert your query to a vector embedding
     2. Search for similar document chunks in Supabase
     3. Retrieve the most relevant chunks
     4. Generate an answer based on the retrieved content
     ```
   - **Added to:** `trace.thinking_log.append(...)`
   - **Calls:** `run_agentic_rag(question="Find me a project with a sandwich wall", session_id="session_123", data_sources={"project_db": True, "code_db": False, "coop_manual": False})`

**Logs created:** 
- ✅ Strategic Planning log (line 5331)
- ✅ Starting RAG Search log (line 5360)

---

## 🔄 Step 6: RAG System - Query Rewriting

**Location:** `localagent/agents/search_orchestrator.py` line 4804-4976  
**Function:** `run_agentic_rag(question, session_id, data_sources)`

### Process:

1. **Build LangGraph Workflow** (line 4823)
   - Creates graph: `plan → route → retrieve → grade → answer → verify → correct`
   - Graph compiled with memory checkpointing

2. **Query Rewriting** (line 4870-4883)
   - **Calls:** `intelligent_query_rewriter(enhanced_question="Find me a project with a sandwich wall", session_id="session_123")`
   - **Location:** `search_orchestrator.py` line 615-782
   - **Process:**
     - Checks for explicit project IDs (regex: `\d{2}-\d{2}-\d{3}`) → None found
     - Gets conversation context from session memory → Empty (first query)
     - **LLM Call** (gpt-4o-mini) at line 659-777
       - **Prompt:** Asks if query is a follow-up, rewrites query
       - **LLM decides:** `is_followup: false` (standalone query)
       - **LLM rewrites:** "Find me a project with a sandwich wall" (unchanged, no follow-up)
     - **Returns:** `("Find me a project with a sandwich wall", {})`
   - **LOG CREATED:** (line 4871-4874)
     ```
     🎯 QUERY REWRITING INPUT: 'Find me a project with a sandwich wall'
     🎯 QUERY REWRITING OUTPUT: 'Find me a project with a sandwich wall'
     🎯 QUERY FILTERS: {}
     🎯 FINAL QUERY FOR RAG: 'Find me a project with a sandwich wall'
     ```
   - **Note:** These logs go to `log_query.info()` (backend console), NOT to `trace.thinking_log` (frontend logs)

3. **Initialize RAG State** (line 4888-4904)
   - Creates `RAGState` with:
     - `user_query = "Find me a project with a sandwich wall"`
     - `data_sources = {"project_db": True, "code_db": False, "coop_manual": False}`
     - `project_filter = None`
     - All other fields empty

4. **Invoke LangGraph** (line 4907)
   - Calls: `graph.invoke(asdict(init), config={"configurable": {"thread_id": session_id}})`
   - LangGraph executes nodes in sequence: `plan → route → retrieve → grade → answer → verify → correct`

**Logs created:** 
- ✅ Query rewriting logs (backend console only, not frontend)

---

## 📋 Step 7: RAG System - Planning Node

**Location:** `localagent/agents/search_orchestrator.py` line 3528-3625  
**Function:** `node_plan(state: RAGState)`

### Process:

1. **Parallel LLM Calls** (line 3578-3583)
   - **Plan Task** (line 3533-3547):
     - Gets conversation context (empty for first query)
     - **LLM Call** (gpt-4o-mini) with `PLANNER_PROMPT`
     - **Prompt:** Asks to create executable query plan with RETRIEVE, EXTRACT, LIMIT_PROJECTS ops
     - **LLM Response:**
       ```json
       {
         "reasoning": "User wants to find projects with sandwich wall feature. Need to search documents for 'sandwich wall' mentions.",
         "steps": [
           {"op": "RETRIEVE", "args": {"queries": ["sandwich wall", "sandwich wall construction", "sandwich wall design"]}},
           {"op": "EXTRACT", "args": {"target": "projects with sandwich wall"}},
           {"op": "LIMIT_PROJECTS", "args": {"n": "infer"}}
         ],
         "subqueries": ["sandwich wall", "sandwich wall construction", "sandwich wall design"]
       }
       ```
   - **Route Task** (line 3549-3575):
     - **LLM Call** (gpt-4o-mini) with `ROUTER_PROMPT`
     - **Prompt:** Asks to choose "smart" or "large" table
     - **LLM Response:** `"smart"` (for specific feature search, smart table is better)
     - **Returns:** `{"data_route": "smart", "project_filter": None}`

2. **Parse & Normalize Plan** (line 3589-3625)
   - Parses JSON from planner LLM
   - Normalizes plan structure
   - **LOG CREATED:** (line 3603-3624)
     ```
     🎯 PLANNING DETAILS:
        Reasoning: User wants to find projects with sandwich wall feature...
        Number of steps: 3
        Step 1: RETRIEVE
           - queries: 3 queries
        Step 2: EXTRACT
           - target: projects with sandwich wall
        Step 3: LIMIT_PROJECTS
           - n: infer
     🔍 SUBQUERIES FORMED (3 total):
        [1] sandwich wall
        [2] sandwich wall construction
        [3] sandwich wall design
     ```
   - **Note:** These logs go to `log_query.info()` (backend console), NOT to `trace.thinking_log` (frontend logs)

3. **Returns:** `{"query_plan": {...}, "data_route": "smart", "project_filter": None}`

**Logs created:** 
- ✅ Planning details logs (backend console only, not frontend)

---

## 🗺️ Step 8: RAG System - Route Node

**Location:** `localagent/agents/search_orchestrator.py` line 3627-3680  
**Function:** `node_route(state: RAGState)`

### Process:

1. **Returns Parallel Route Result** (line 3680)
   - Already computed in `node_plan` (parallel execution)
   - Returns: `{"data_route": "smart", "project_filter": None}`
   - **LOG CREATED:** (line 3569-3570, backend console)
     ```
     🎯 ROUTER DECISION: 'Find me a project with a sandwich wall...' → 'smart' → 'smart'
        LLM choice: 'smart' | Allowed: True | Final route: 'smart'
     ```

**Logs created:** 
- ✅ Router decision log (backend console only, not frontend)

---

## 🔎 Step 9: RAG System - Retrieve Node

**Location:** `localagent/agents/search_orchestrator.py` line 3880-4076  
**Function:** `node_retrieve(state: RAGState)`

### Process:

1. **Execute Plan** (line 3885-3923)
   - **Calls:** `execute_plan(state)` (line 3682-3878)
   - **Process:**
     - Iterates through plan steps:
       - **Step 1: RETRIEVE** (line 3700-3770)
         - For each query in `["sandwich wall", "sandwich wall construction", "sandwich wall design"]`:
           - **Vector Search** (line 3730-3750):
             - Embeds query using `OpenAIEmbeddings`
             - Searches `vs_smart` vector store (Supabase `smart_chunks` table)
             - **Query:** `vs_smart.similarity_search("sandwich wall", k=20)`
             - **Returns:** Top 20 document chunks with highest similarity scores
             - **Chunks contain:** Text content, project IDs (e.g., "25-07-118"), page numbers, metadata
           - **LOG CREATED:** (line 3735-3740, backend console)
             ```
             🔍 RETRIEVING: query='sandwich wall', k=20, route=smart
             📊 Retrieved 20 chunks from smart table
             ```
         - Combines results from all 3 queries
         - Deduplicates by chunk ID
         - **Total retrieved:** ~50-60 chunks (some overlap between queries)
       - **Step 2: EXTRACT** (skipped in retrieve - happens in synthesis)
       - **Step 3: LIMIT_PROJECTS** (skipped in retrieve - happens in synthesis)

2. **Log Retrieved Chunks** (line 3895-3903)
   - **LOG CREATED:** (line 3896, backend console)
     ```
     RETRIEVED CHUNKS: 50 total from 50 projects
     ```
   - **Detailed logging:** (line 3896-3903)
     - Logs each chunk with project ID, page number, snippet
     - **Note:** These logs go to backend console, NOT frontend

3. **Returns:** `{"retrieved_docs": [Document(...), Document(...), ...]}`

**Logs created:** 
- ✅ Retrieval logs (backend console only, not frontend)
- ✅ Retrieved chunks count (backend console only, not frontend)

---

## ✅ Step 10: RAG System - Grade Node

**Location:** `localagent/agents/search_orchestrator.py` line 4132-4204  
**Function:** `node_grade(state: RAGState)`

### Process:

1. **Self-Grade Documents** (line 4152-4154)
   - **Calls:** `self_grade(state.user_query, state.retrieved_docs)` (line 3682-3878)
   - **Process:**
     - **LLM Call** (gpt-4o-mini) for each document chunk
     - **Prompt:** "Is this document relevant to the query 'Find me a project with a sandwich wall'? Score 0-1."
     - **LLM scores:** Each chunk gets relevance score (0.0-1.0)
     - **Filters:** Keeps only chunks with score >= 0.7 (or top 50 if `USE_GRADER=False`)
   - **LOG CREATED:** (line 4153-4154, backend console)
     ```
     Running self_grade on project docs...
     Graded (filtered): 45 docs from 45 projects
     ```
   - **Note:** These logs go to backend console, NOT frontend

2. **Returns:** `{"graded_docs": [Document(...), Document(...), ...]}` (filtered to top 45)

**Logs created:** 
- ✅ Grading logs (backend console only, not frontend)

---

## 📝 Step 11: RAG System - Answer Node (Synthesis)

**Location:** `localagent/agents/search_orchestrator.py` line 4207-4400  
**Function:** `node_answer(state: RAGState)`

### Process:

1. **Prepare Documents** (line 4210-4221)
   - Gets `graded_docs` (45 filtered chunks)
   - Checks if user asked for specific number of projects → None (uses "infer")

2. **Synthesize Answer** (line 4240-4270)
   - **Calls:** `synthesize(q, docs, session_id, ...)` (line 3006-3399)
   - **Location:** `search_orchestrator.py` line 3006-3399
   - **Process:**
     - **Groups documents by project** (line 3041-3055)
       - Extracts project IDs from metadata (e.g., "25-07-118", "25-08-205")
       - Groups chunks by project
     - **Fetches project metadata** (line 3057-3100)
       - For each unique project ID, queries Supabase `project_info` table
       - Gets: dimensions, building type, material, location, etc.
     - **LLM Call** (gpt-4o-mini) at line 3102-3200
       - **Prompt:** `ANSWER_PROMPT` with:
         - User query: "Find me a project with a sandwich wall"
         - Retrieved documents: 45 chunks grouped by project
         - Project metadata: Dimensions, types, materials for each project
       - **LLM Response:**
         ```markdown
         Based on the retrieved documents, I found the following projects with sandwich walls:
         
         1. **Project 25-07-118** (Residential, 50' x 100')
            - Contains sandwich wall construction details
            - Located in [location]
            - [Additional details from documents]
         
         2. **Project 25-08-205** (Commercial, 80' x 120')
            - Features sandwich wall design
            - [Additional details]
         
         [More projects...]
         ```
     - **Extracts citations** (line 3202-3250)
       - Finds project IDs mentioned in answer
       - Creates citation list: `[{"project": "25-07-118", "page": "A-101"}, ...]`
   - **LOG CREATED:** (line 3026-3037, backend console)
     ```
     🔍 SYNTHESIS DEBUG: synthesize() called - use_code_prompt=False, docs=45
     🔍 SYNTHESIS DEBUG: active_filters=None
     ```
   - **Note:** These logs go to backend console, NOT frontend

3. **Returns:** `{"final_answer": "...", "answer_citations": [...]}`

**Logs created:** 
- ✅ Synthesis logs (backend console only, not frontend)
- ✅ **ANSWER GENERATED:** Full answer text with project details

---

## ✔️ Step 12: RAG System - Verify Node

**Location:** `localagent/agents/search_orchestrator.py` line 4481-4600  
**Function:** `node_verify(state: RAGState)`

### Process:

1. **Create Document Index** (line 4493)
   - **Calls:** `_make_doc_index(state.graded_docs)` (line 4463-4473)
   - Creates summary: `"25-07-118 | page=A-101 | date=2025-01-15 | sandwich wall construction details..."`

2. **LLM Verification** (line 4494-4496)
   - **LLM Call** (gpt-4o-mini) with `VERIFY_PROMPT`
   - **Prompt:** Asks if answer needs fixing (missing projects, duplicates, count mismatch)
   - **LLM Response:**
     ```json
     {
       "needs_fix": false,
       "projects": ["25-07-118", "25-08-205", ...],
       "note": "Answer correctly lists projects with sandwich walls"
     }
     ```
   - **LOG CREATED:** (line 4504, backend console)
     ```
     <<< VERIFY DONE (no fix needed) in 0.5s
     ```

3. **Returns:** `{"needs_fix": false}`

**Logs created:** 
- ✅ Verification logs (backend console only, not frontend)

---

## 🔄 Step 13: RAG System - Correct Node (Final)

**Location:** `localagent/agents/search_orchestrator.py` line 4602-4680  
**Function:** `node_correct(state: RAGState)`

### Process:

1. **Returns Final State** (line 4602-4680)
   - Since `needs_fix = false`, just returns final answer as-is
   - **Returns:** `{"final_answer": state.final_answer, "answer_citations": state.answer_citations}`

2. **LangGraph Completes** (line 4907)
   - Graph execution finishes
   - Returns final state with answer

**Logs created:** None (final step)

---

## 📤 Step 14: RAG System - Return Results

**Location:** `localagent/agents/search_orchestrator.py` line 4907-4976  
**Function:** `run_agentic_rag(...)`

### Process:

1. **Extract Final Answer** (line 4944-4976)
   - Gets `final_state.final_answer` (the synthesized answer from Step 11)
   - Gets `final_state.answer_citations` (list of citations)
   - Extracts project IDs from answer text (regex: `\d{2}-\d{2}-\d{3}`)

2. **Update Session Memory** (line 4966-4999)
   - Stores conversation history
   - Updates `SESSION_MEMORY[session_id]`

3. **Returns:**
   ```python
   {
     "answer": "Based on the retrieved documents, I found the following projects with sandwich walls:\n\n1. **Project 25-07-118** (Residential, 50' x 100')\n...",
     "citations": [{"project": "25-07-118", "page": "A-101"}, ...],
     "support": 0.85,  # Average relevance score
     "route": "smart"
   }
   ```

**Logs created:** None (returning results)

---

## 📊 Step 15: SearchOrchestrator - Process RAG Results

**Location:** `localagent/agents/search_orchestrator.py` line 5378-5400  
**Function:** `SearchOrchestrator.execute(...)`

### Process:

1. **Extract Answer** (line 5378-5379)
   - Gets `answer = rag_result.get('answer', '')`
   - Gets `citations = rag_result.get('citations', [])`

2. **Create RAG Complete Log** (line 5381)
   - **LOG CREATED:**
     ```markdown
     ## ✅ RAG Search Complete
     
     **Results:**
     - Answer generated: 5680 characters
     - Citations found: 50 documents
     
     **What happened:**
     1. ✅ Query embedded successfully
     2. ✅ Searched Supabase vector stores
     3. ✅ Retrieved 50 relevant document chunks
     4. ✅ Generated answer from retrieved content
     
     *Note: The final answer is shown in the chat panel. This log shows the process, not the answer itself.*
     ```
   - **Added to:** `trace.thinking_log.append(...)`

3. **Check for Empty Answer** (line 5383-5390)
   - If answer is empty, creates warning log
   - **In this case:** Answer exists, so no warning

4. **Returns:** `{"answer": "...", "citations": [...], "thinking_logs": trace.thinking_log}`

**Logs created:** 
- ✅ RAG Search Complete log (line 5381) → **SHOWN IN FRONTEND**

---

## 🔙 Step 16: Backend - Format Response

**Location:** `backend/main.py` line 256-427  
**Function:** `chat()` endpoint

### Process:

1. **Extract Thinking Logs** (line 260-266)
   - Gets `trace.thinking_log` from SearchOrchestrator result
   - Converts to AgentLog format:
     ```python
     thinking_logs = [
       {
         "type": "thinking",
         "thinking": "## 🎯 Strategic Planning\n\n...",
         "timestamp": "2025-01-15T10:30:00"
       },
       {
         "type": "thinking",
         "thinking": "## 📚 Starting RAG Search\n\n...",
         "timestamp": "2025-01-15T10:30:01"
       },
       {
         "type": "result",
         "thinking": "## ✅ RAG Search Complete\n\n...",
         "timestamp": "2025-01-15T10:30:15"
       }
     ]
     ```

2. **Extract Execution Steps** (line 269-298)
   - Gets `trace.steps` (list of ExecutionStep objects)
   - Formats each step as log entry
   - **In this case:** No explicit steps logged (RAG handles internally)

3. **Format Planning Information** (line 300-318)
   - Creates formatted planning log from TeamOrchestrator
   - **LOG CREATED:**
     ```markdown
     ## 🎯 Strategic Planning
     
     **Intent:** project_search
     **Data Sources:** supabase_metadata, rag_documents
     **Strategy:** metadata_first
     **Reasoning:** User wants to find projects with specific feature...
     ```
   - **Added to:** `thinking_logs.insert(0, {...})`

4. **Extract Final Answer** (line 320-406)
   - Gets `answer` from `result["results"]["answer"]`
   - **Answer:** "Based on the retrieved documents, I found the following projects with sandwich walls:\n\n1. **Project 25-07-118**..."

5. **Return JSON Response** (line 417-427)
   ```json
   {
     "reply": "Based on the retrieved documents, I found the following projects with sandwich walls:\n\n1. **Project 25-07-118**...",
     "thinking_logs": [...],
     "planning": {...},
     "routing": {...},
     "citations": 50
   }
   ```

**Logs created:** 
- ✅ Planning information log (formatted for frontend)
- ✅ Final answer extracted

---

## 🖥️ Step 17: Frontend - Display Results

**Location:** `Frontend/components/SmartChatPanel.vue` line 405-470  
**Function:** `handleSend()`

### Process:

1. **Receive Response** (line 421-446)
   - Gets JSON response from backend
   - Extracts `reply` (final answer)
   - Extracts `thinking_logs` (array of log entries)

2. **Emit Logs** (line 427-434)
   - For each log in `thinking_logs`:
     - Emits `'agent-log'` event to parent (`index.vue`)
     - **Logs shown in:** `AgentLogsPanel.vue` (left panel)

3. **Display Answer** (line 443-450)
   - Adds message to `messages` array
   - **Answer shown in:** `SmartChatPanel.vue` (right panel, chat interface)

**Logs displayed:**
- ✅ Strategic Planning log (in logs panel)
- ✅ Starting RAG Search log (in logs panel)
- ✅ RAG Search Complete log (in logs panel)

**Answer displayed:**
- ✅ Full answer text (in chat panel)

---

## 📋 Summary: Where Logs Are Created

### Frontend Logs (Shown in AgentLogsPanel):
1. **Strategic Planning** → `search_orchestrator.py:5331` → `trace.thinking_log.append(...)`
2. **Starting RAG Search** → `search_orchestrator.py:5360` → `trace.thinking_log.append(...)`
3. **RAG Search Complete** → `search_orchestrator.py:5381` → `trace.thinking_log.append(...)`
4. **Planning Information** → `backend/main.py:300-318` → Formatted from TeamOrchestrator planning

### Backend Console Logs (NOT shown in frontend):
- Query rewriting logs → `search_orchestrator.py:4871-4874` → `log_query.info(...)`
- Planning details → `search_orchestrator.py:3603-3624` → `log_query.info(...)`
- Router decision → `search_orchestrator.py:3569-3570` → `log_route.info(...)`
- Retrieval logs → `search_orchestrator.py:3735-3740` → `log_query.info(...)`
- Grading logs → `search_orchestrator.py:4153-4154` → `log_enh.info(...)`
- Synthesis logs → `search_orchestrator.py:3026-3037` → `log_query.info(...)`
- Verification logs → `search_orchestrator.py:4504` → `log_enh.info(...)`

### Answer Generation:
- **Location:** `search_orchestrator.py:3006-3399` → `synthesize()` function
- **Process:** LLM call with retrieved documents + project metadata
- **Output:** Full answer text with project details and citations

---

## 🎯 Key Decision Points

| Decision | Location | Method | Result for "sandwich wall" |
|----------|----------|--------|---------------------------|
| **Intent Classification** | `team_orchestrator.py:98-141` | LLM (gpt-4o-mini) | `project_search` |
| **Data Source Selection** | `team_orchestrator.py:98-141` | LLM (gpt-4o-mini) | `["supabase_metadata", "rag_documents"]` |
| **Strategy Selection** | `team_orchestrator.py:98-141` | LLM (gpt-4o-mini) | `metadata_first` |
| **Agent Routing** | `team_orchestrator.py:184-204` | LLM (gpt-4o-mini) | `"search"` → SearchOrchestrator |
| **Query Rewriting** | `search_orchestrator.py:615-782` | LLM (gpt-4o-mini) | Unchanged (not follow-up) |
| **Query Planning** | `search_orchestrator.py:3528-3625` | LLM (gpt-4o-mini) | 3 subqueries: ["sandwich wall", "sandwich wall construction", "sandwich wall design"] |
| **Table Routing** | `search_orchestrator.py:3549-3575` | LLM (gpt-4o-mini) | `"smart"` table |
| **Document Retrieval** | `search_orchestrator.py:3880-4076` | Vector search (Supabase) | ~50 chunks retrieved |
| **Document Grading** | `search_orchestrator.py:4132-4204` | LLM (gpt-4o-mini) | 45 chunks kept (filtered) |
| **Answer Synthesis** | `search_orchestrator.py:3006-3399` | LLM (gpt-4o-mini) | Full answer with project details |
| **Answer Verification** | `search_orchestrator.py:4481-4600` | LLM (gpt-4o-mini) | No fix needed |

---

## 🔍 How the Answer is Actually Made

1. **Query Embedding:** "Find me a project with a sandwich wall" → Vector embedding (1536 dimensions)

2. **Vector Search:** Searches Supabase `smart_chunks` table for similar vectors → Returns top 50 chunks

3. **Document Grading:** LLM scores each chunk for relevance → Keeps top 45 chunks

4. **Grouping:** Groups chunks by project ID (e.g., "25-07-118", "25-08-205")

5. **Metadata Fetching:** Queries Supabase `project_info` table for each project → Gets dimensions, types, materials

6. **Answer Synthesis:** LLM (gpt-4o-mini) receives:
   - User query: "Find me a project with a sandwich wall"
   - Retrieved chunks: 45 chunks grouped by project
   - Project metadata: Dimensions, types, materials for each project
   - **LLM generates:** Full answer text listing projects with sandwich walls, including details from metadata

7. **Citation Extraction:** Extracts project IDs and page numbers from answer → Creates citation list

8. **Verification:** LLM verifies answer is complete and correct → No fixes needed

9. **Final Answer:** Returns formatted answer with citations

---

## 📝 Notes

- **Frontend logs** (`trace.thinking_log`) are shown in the AgentLogsPanel
- **Backend console logs** (`log_query.info`, `log_enh.info`, etc.) are NOT shown in frontend
- **Answer generation** happens in the `synthesize()` function via LLM call with retrieved documents
- **All decisions** are made by LLM calls (gpt-4o-mini) except vector search (Supabase similarity search)




