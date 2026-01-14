# Memory & Follow-Up Detection Flow - Complete Walkthrough

## Overview
This document explains how conversation memory is maintained and how follow-up questions are detected and handled in the RAG system.

---

## 🏗️ Architecture Components

### 1. **Checkpointer** (`nodes/DBRetrieval/KGdb/checkpointer.py`)
- **Purpose**: LangGraph's persistence layer that automatically saves state after each graph execution
- **Current Implementation**: `MemorySaver` (in-memory only, lost on restart)
- **Future**: `SqliteSaver` (persistent file-based storage)
- **How it works**: Automatically saves the entire `RAGState` after each node execution

### 2. **RAGState** (`models/rag_state.py`)
- **Key Fields**:
  - `conversation_history: List[Dict]` - Stores all Q&A exchanges
  - `original_question: str` - User's original question (before rewriting)
  - `user_query: str` - Rewritten/enhanced query (used for retrieval)
- **Each exchange format**:
  ```python
  {
    "question": "Find me 3 projects with floating slabs",
    "answer": "3 projects have floating slabs...",
    "timestamp": 1234567890.123,
    "projects": ["25-01-064", "25-01-070", "25-01-028"]
  }
  ```

### 3. **Query Rewriter** (`models/memory.py::intelligent_query_rewriter`)
- **Purpose**: Detects follow-ups and rewrites queries with context
- **Input**: User query + conversation history
- **Output**: Rewritten query + project filters

### 4. **Correct Node** (`nodes/DBRetrieval/SQLdb/correct.py`)
- **Purpose**: Updates conversation history after each exchange
- **Runs**: Last in the graph (has access to final answer)

---

## 🔄 Complete Flow: Step-by-Step

### **STEP 1: User Asks First Question**
```
User: "Find me 3 projects with floating slabs"
```

### **STEP 2: Load Previous State** (`main.py` lines 101-118)
```python
# Get previous state from checkpointer using thread_id (session_id)
state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})

if state_snapshot and state_snapshot.values:
    previous_state = state_snapshot.values
    conversation_history = previous_state.get("conversation_history", [])
else:
    conversation_history = []  # First invocation - no history
```

**Result**: `conversation_history = []` (empty, first question)

---

### **STEP 3: Query Rewriting with Follow-Up Detection** (`main.py` lines 125-129)
```python
rewritten_query, query_filters = intelligent_query_rewriter(
    enhanced_question, 
    session_id,
    conversation_history=conversation_history  # Pass loaded history
)
```

**Inside `intelligent_query_rewriter`** (`models/memory.py` lines 136-320):

#### 3a. Extract Projects from History
```python
if conversation_history:
    # Get projects from last 5 exchanges
    for exchange in conversation_history[-5:]:
        projects = exchange.get("projects", [])
        recent_projects.extend(projects)
    
    # Get most recent exchange
    last_exchange = conversation_history[-1]
    last_answer_projects = last_exchange.get("projects", [])
    last_query_text = last_exchange.get("question", "")
```

**Result for first question**: 
- `recent_projects = []`
- `last_answer_projects = []`
- `last_query_text = ""`

#### 3b. Build Focus Context
```python
focus_state = {
    "recent_projects": recent_projects,           # Projects from last 5 exchanges
    "last_answer_projects": last_answer_projects, # Projects from most recent answer
    "last_query_text": last_query_text            # Most recent question
}
```

#### 3c. Format Conversation History for LLM
```python
conversation_context_str = ""
if conversation_history:
    for i, exchange in enumerate(conversation_history[-3:], 1):
        conversation_context_str += f"\nExchange {i}:\n"
        conversation_context_str += f"  Q: {exchange['question']}\n"
        conversation_context_str += f"  A: {exchange['answer'][:200]}...\n"
        conversation_context_str += f"  Projects: {exchange['projects']}\n"
```

**Result for first question**: Empty string (no history)

#### 3d. LLM Follow-Up Detection
The LLM receives:
- Current query: `"Find me 3 projects with floating slabs"`
- Conversation history: (empty for first question)
- Focus context: (empty for first question)

**LLM Analysis**:
- `is_followup = false` (no prior context)
- `confidence = 0.0`
- `rewritten_query = "Find me 3 projects with floating slabs"` (unchanged)

**Result**: Query passes through unchanged, no project filters

---

### **STEP 4: Initialize RAGState** (`main.py` lines 153-170)
```python
init = RAGState(
    session_id=session_id,
    user_query=base_query,              # Rewritten query: "Find me 3 projects..."
    original_question=question,          # Original: "Find me 3 projects..."
    conversation_history=init_conversation_history  # Loaded from checkpointer: []
)
```

---

### **STEP 5: Execute Graph** (`main.py` line 176)
```python
final = graph.invoke(
    asdict(init), 
    config={"configurable": {"thread_id": session_id}}
)
```

**Graph Flow**:
1. `plan` → `rag` → `retrieve` → `grade` → `answer` → `verify` → `correct`
2. **Checkpointer automatically saves state after each node**
3. Each node receives state with `conversation_history = []`

---

### **STEP 6: Update Conversation History** (`correct.py` lines 55-93)

**Runs LAST** in the graph (has access to final answer):

```python
# Get current conversation history from state
conversation_history = list(state.conversation_history or [])

# Build full answer text
answer_text = state.final_answer or ""
if state.code_answer:
    answer_text += f"\n\n--- Code References ---\n\n{state.code_answer}"

# Extract projects from answer
projects_in_answer = []
for match in PROJECT_RE.finditer(answer_text):
    projects_in_answer.append(match.group(0))

# Add new exchange
new_exchange = {
    "question": state.original_question,  # "Find me 3 projects..."
    "answer": answer_text,                  # "3 projects have floating slabs..."
    "timestamp": time.time(),
    "projects": ["25-01-064", "25-01-070", "25-01-028"]
}
conversation_history.append(new_exchange)

# Maintain sliding window (keep last 10 exchanges)
if len(conversation_history) > MAX_CONVERSATION_HISTORY:
    conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]

# Return updated history
return {"conversation_history": conversation_history}
```

**Result**: 
```python
conversation_history = [
    {
        "question": "Find me 3 projects with floating slabs",
        "answer": "3 projects have floating slabs...",
        "timestamp": 1234567890.123,
        "projects": ["25-01-064", "25-01-070", "25-01-028"]
    }
]
```

**Checkpointer automatically saves this updated state!**

---

### **STEP 7: User Asks Follow-Up**
```
User: "Tell me more about the last mentioned project"
```

### **STEP 8: Load Previous State Again** (`main.py` lines 101-118)
```python
state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})
previous_state = state_snapshot.values
conversation_history = previous_state.get("conversation_history", [])
```

**Result**: 
```python
conversation_history = [
    {
        "question": "Find me 3 projects with floating slabs",
        "answer": "3 projects have floating slabs...",
        "projects": ["25-01-064", "25-01-070", "25-01-028"]
    }
]
```

---

### **STEP 9: Follow-Up Detection** (`models/memory.py` lines 220-320)

#### 9a. Extract Context
```python
# From conversation_history
last_exchange = conversation_history[-1]
last_answer_projects = ["25-01-064", "25-01-070", "25-01-028"]
last_query_text = "Find me 3 projects with floating slabs"

focus_state = {
    "recent_projects": ["25-01-064", "25-01-070", "25-01-028"],
    "last_answer_projects": ["25-01-064", "25-01-070", "25-01-028"],
    "last_query_text": "Find me 3 projects with floating slabs"
}
```

#### 9b. Format for LLM
```python
conversation_context_str = """
RECENT CONVERSATION HISTORY:

Exchange 1:
  Q: Find me 3 projects with floating slabs
  A: 3 projects have floating slabs...
  Projects mentioned: 25-01-064, 25-01-070, 25-01-028
"""
```

#### 9c. LLM Analysis
**LLM receives**:
- Current query: `"Tell me more about the last mentioned project"`
- Conversation history: (shown above)
- Focus context: Projects `["25-01-064", "25-01-070", "25-01-028"]`

**LLM Analysis**:
- **Follow-up indicators detected**:
  - "the last mentioned project" = positional reference
  - Query is incomplete without context
- **Decision**: `is_followup = true`, `confidence = 0.95`
- **Project resolution**: "last mentioned" = most recent = `"25-01-028"` (last in list)
- **Rewritten query**: `"Tell me more about project 25-01-028"`
- **Filters**: `{"project_keys": ["25-01-028"]}`

**Result**: 
```python
rewritten_query = "Tell me more about project 25-01-028"
query_filters = {"project_keys": ["25-01-028"]}
```

---

### **STEP 10: Execute with Context**
```python
init = RAGState(
    user_query="Tell me more about project 25-01-028",  # Rewritten
    original_question="Tell me more about the last mentioned project",  # Original
    conversation_history=[...]  # Loaded from checkpointer
)
```

Graph executes with project filter `25-01-028`, retrieves relevant docs, generates answer.

---

### **STEP 11: Update History Again** (`correct.py`)
```python
conversation_history = [
    {
        "question": "Find me 3 projects with floating slabs",
        "answer": "3 projects have floating slabs...",
        "projects": ["25-01-064", "25-01-070", "25-01-028"]
    },
    {
        "question": "Tell me more about the last mentioned project",  # Original!
        "answer": "Project 25-01-028 is Rob Lachapelle...",
        "projects": ["25-01-028"]
    }
]
```

**Checkpointer saves this updated state!**

---

## 🔑 Key Design Decisions

### 1. **Why `original_question` is Stored Separately**
- `user_query` contains the **rewritten** query (e.g., "Tell me more about project 25-01-028")
- `original_question` contains the **user's actual question** (e.g., "Tell me more about the last mentioned project")
- **Reason**: Conversation history should show what the user actually asked, not the internal rewrite

### 2. **Why Conversation History is Updated in `correct.py`**
- `correct.py` runs **last** in the graph
- It has access to:
  - Final answer (from `answer` node)
  - Code answer (if any)
  - Coop answer (if any)
  - Original question (from state)
- **Single source of truth**: Only one place updates history (no duplication)

### 3. **Why Checkpointer is Used**
- **Automatic persistence**: LangGraph automatically saves state after each node
- **Thread-based**: Each `session_id` is a separate thread
- **State recovery**: Can resume from any checkpoint
- **No manual save/load**: Just use `graph.get_state()` to load

### 4. **Why Follow-Up Detection Happens Before Graph**
- Query rewriting needs to happen **before** retrieval
- If it's a follow-up, we need to:
  - Add project filters
  - Rewrite the query with context
  - Route to correct databases
- **Timing**: Load history → Rewrite query → Execute graph

---

## 🐛 Common Issues & Solutions

### Issue 1: "Last mentioned project" refers to wrong project
**Cause**: Using first project instead of last project from `last_answer_projects`

**Fix**: Use `last_answer_projects[-1]` (most recent = last in list)

### Issue 2: Conversation history lost on restart
**Cause**: Using `MemorySaver` (in-memory only)

**Fix**: Install `langgraph-checkpoint-sqlite` and switch to `SqliteSaver`

### Issue 3: Duplicate exchanges in history
**Cause**: Both `correct.py` and `main.py` were updating history

**Fix**: Only `correct.py` updates history now (removed duplicate in `main.py`)

### Issue 4: Follow-up detection not working
**Cause**: `intelligent_query_rewriter` wasn't receiving conversation history

**Fix**: Load history from checkpointer **before** calling rewriter, pass it as parameter

---

## 📊 Memory Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ASKS QUESTION                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Load Previous State from Checkpointer               │
│  - graph.get_state({"thread_id": session_id})                 │
│  - Extract conversation_history                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Query Rewriting with Follow-Up Detection            │
│  - intelligent_query_rewriter(query, conversation_history)   │
│  - Extract projects from history                             │
│  - LLM analyzes if follow-up                                 │
│  - Rewrite query + add project filters                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Initialize RAGState                                 │
│  - user_query = rewritten_query                              │
│  - original_question = user's actual question                 │
│  - conversation_history = loaded from checkpointer            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Execute Graph                                       │
│  - plan → rag → retrieve → grade → answer → verify → correct │
│  - Checkpointer saves state after each node                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Update Conversation History (correct.py)            │
│  - Extract projects from answer                              │
│  - Add new exchange: {question, answer, projects, timestamp}│
│  - Maintain sliding window (keep last 10)                    │
│  - Return updated conversation_history                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Checkpointer Automatically Saves State              │
│  - conversation_history persisted for next invocation        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Verification Checklist

To verify memory is working correctly:

1. **First question**: Should have empty `conversation_history`
2. **After first answer**: `conversation_history` should have 1 exchange
3. **Follow-up question**: Should load previous history, detect follow-up, rewrite query
4. **After follow-up answer**: `conversation_history` should have 2 exchanges
5. **Original questions preserved**: History should show user's actual questions, not rewritten ones
6. **Projects extracted**: Each exchange should have `projects` list from answer text
7. **Sliding window**: After 10+ exchanges, oldest should be dropped

---

## 🚀 Next Steps

1. **Enable persistent storage**: Install `langgraph-checkpoint-sqlite`
2. **Monitor memory usage**: Check `conversation_history` length in logs
3. **Test follow-up detection**: Try various follow-up patterns
4. **Clean up old code**: Remove `SESSION_MEMORY` conversation_history updates (keep only for semantic intelligence)
