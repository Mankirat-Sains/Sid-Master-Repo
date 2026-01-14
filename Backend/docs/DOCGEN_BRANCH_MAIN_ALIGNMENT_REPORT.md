# DOCGEN Branch Main Alignment Report

## Main Conformity Checklist
- ✅ Conversation history now flows through `ParentState` and checkpointer: query rewriter accepts `messages`/`conversation_history` and both chat/streaming entrypoints seed messages with the current user turn (`Backend/models/memory.py`, `Backend/main.py`, `Backend/api_server.py`).
- ✅ DB retrieval subgraph returns persisted memory: `node_correct` writes messages + structured `conversation_history` with a sliding window and the wrapper propagates them back to the parent state (`Backend/nodes/DBRetrieval/SQLdb/correct.py`, `Backend/graph/subgraphs/db_retrieval_subgraph.py`).
- ✅ Doc generation participates in memory flow: docgen subgraph now accepts parent messages/history and writes them back so docgen exchanges are checkpointed (`Backend/graph/subgraphs/document_generation_subgraph.py`).
- ✅ Streaming aligned to parent graph architecture: uses `ParentState`, pulls conversation history from the checkpointer, respects `db_retrieval_*` result fields, and keeps token streaming single-sourced from LangGraph (custom token streaming suppressed for doc workflows to avoid duplication) (`Backend/api_server.py`).
- ✅ Response payload parity: streaming responses now include `execution_trace`/`node_path` and prefer aggregated `db_retrieval_*` fields to match non-streaming chat behavior (`Backend/api_server.py`).
- ⚠️ Tests not executed here because `pytest` is not installed in the environment; manual verification recommended after installing it.

## Docgen Workflow Wiring
- Entry: `plan` selects routers → `doc_task_classifier` detects docgen intent (workflow `docgen`, `task_type` set).
- Docgen branch: `desktop_agent` subgraph → `doc_generation` subgraph (plan → generate section/report → answer adapter → verify/correct). `doc_correct` appends the assistant turn plus metadata to `messages` and `conversation_history`, which the parent checkpointer persists.
- QA/RAG branch: `router_dispatcher` (selected_routers) → `db_retrieval` subgraph (rag_plan/router → retrieve → grade → answer → verify → correct). `node_correct` now records question/answer exchanges and messages for checkpointer memory.
- Memory: both branches seed messages with the new user turn before graph execution; conversation history is truncated to `MAX_CONVERSATION_HISTORY` and returned to the parent state so subsequent calls load the same context via checkpointer.

## API / Front-End Integration Notes
- Streaming (`/chat/stream`) now initializes from checkpointer messages/history, uses `ParentState`, and emits SSE updates with `execution_trace` and `node_path` for UI tracing. Token streaming relies on LangGraph `messages` mode; custom token streaming is suppressed for doc workflows to avoid double-streaming.
- Non-streaming `/chat` path continues to materialize OnlyOffice previews when `doc_generation_result` is present; streaming responses include `doc_generation_result`/`doc_generation_warnings` and route/citation fields derived from `db_retrieval_*` outputs.
- Document preview payloads remain unchanged; docgen runs continue to call `materialize_onlyoffice_document` when appropriate.

## Manual Test Plan
- **Info retrieval (QA)**: run `/chat/stream` or `/chat` with a standard question; confirm citations, `execution_trace`, and that follow-up questions reuse prior answers (conversation history visible in logs).
- **Doc generation**: ask for a report/section; verify routing to docgen (workflow `docgen`), doc preview materialization, and that conversation history persists the draft exchange.
- **Desktop/agent routing**: issue a doc request mentioning Word/open/save to ensure `doc_task_classifier` sets `requires_desktop_action` and the desktop path runs without affecting QA routing.
- **Doc preview**: after a docgen call, open the OnlyOffice preview in `workspace.vue` and ensure the rendered document matches `doc_generation_result`; repeat a follow-up docgen request to verify the prior draft is in conversation history.
