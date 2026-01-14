# 1) High-Level System Map (As-Built)
Sidian currently runs a LangGraph-driven backend exposed through FastAPI. A chat request enters `Backend/api_server.py` via `/chat` or `/chat/stream`, is pre-processed (query rewriting, optional vision captioning), then passed to a compiled LangGraph (`Backend/graph/builder.py`). The graph performs router selection, doc/QA classification, and dispatches either to the DB retrieval subgraph, the desktop/docgen subgraph, or a multi-router dispatcher. State (messages, routing flags, docgen hints) is threaded through and persisted by the LangGraph checkpointer. Answers are synthesized and streamed back; doc generation may materialize an OnlyOffice doc on disk.

**Current request flow (simplified ASCII):**
```
User → FastAPI (/chat or /chat/stream)
  → query rewrite + image captions (API layer)
  → LangGraph (thread_id = session_id)
      plan (router selection)
      → doc_task_classifier
          → desktop_agent subgraph? (if docgen/workflow/doc hints)
          → router_dispatcher? (if multiple routers chosen)
          → db_retrieval subgraph? (default)
      subgraphs run:
        DBRetrieval: rag_plan_router → [image_embed? → image_similarity] → retrieve → grade → answer → verify → correct
        Desktop/docgen: desktop_router → [doc_plan → doc_generate_section/report → doc_answer_adapter → doc_verify → doc_correct]
      → END
  → Response assembly + Supabase logging + optional OnlyOffice doc build
```

# Phase 3 Deep Agent Updates (Implemented)
- Builder now runs on `RAGState` with trace merging for subgraphs; desktop subgraph routes to deep loop when `DEEP_AGENT_ENABLED`.
- Deep desktop loop added with think–act–observe cycles, workspace management, and interrupt gating for destructive actions.
- API layer exposes `/approve-action` and streams `interrupt` SSE payloads for approvals; state compatibility helpers normalize desktop fields.
- Workspace retention/interrupt/config flags documented in `.env.example` and deep-agent docs (`Docs/Deep_Agent_Architecture.md`, `Docs/Deep_Agent_Usage.md`, `Docs/Interrupt_Handling.md`).

# 2) Repo Structure + Key Modules
- Backend logic lives in `Backend/` (FastAPI server, LangGraph, nodes, state models, prompts, helpers).
- Frontend lives in `Frontend/Frontend/` (not analyzed in depth here).
- Graph orchestration: `Backend/graph/builder.py` plus subgraphs in `Backend/graph/subgraphs/`.
- State models: `Backend/models/parent_state.py`, `Backend/models/db_retrieval_state.py`, `Backend/models/rag_state.py`.
- Retrieval/RAG nodes: `Backend/nodes/DBRetrieval/SQLdb/` (plan/router/retrieve/grade/answer/verify/correct + image nodes).
- Document generation: `Backend/document_generation/` and `Backend/nodes/DesktopAgent/desktop_router.py`.
- Persistence: `Backend/graph/checkpointer.py` (in-memory/sqlite/postgres), Supabase vector stores in `Backend/nodes/DBRetrieval/KGdb/supabase_client.py`.
- Observability: logging config in `Backend/config/logging_config.py`, thinking log generators in `Backend/thinking/`.

# 3) Entry Points + Runtime Lifecycle
- **FastAPI** in `Backend/api_server.py` registers `/chat` (sync) and `/chat/stream` (SSE). `/chat/stream` is the primary path for real-time logs; `/chat` wraps `thinking/rag_wrapper.py` to add post-hoc thinking logs.
- Request model `ChatRequest` includes `message`, `session_id`, optional `data_sources`, and `images_base64`.
- `/chat/stream` pipeline:
  - Loads previous state via `graph.get_state`/`aget_state` using `configurable.thread_id = session_id`.
  - Runs `intelligent_query_rewriter` (`Backend/models/memory.py`) on the user question (+ vision captions) and prior `messages`.
  - Seeds `RAGState` with rewritten query, original question, `messages` (prior + current user message), `data_sources`, image flags.
  - Calls `graph.astream(..., stream_mode=["updates","custom","messages"])`, streaming node updates, custom events, and LLM tokens.
  - Collects final state updates, assembles response (answers, citations, follow-ups, execution_trace, docgen payloads), optionally materializes a docx in `Backend/documents/`.
- `/chat` pipeline:
  - Calls `thinking/rag_wrapper.py::run_agentic_rag_with_thinking_logs`, which invokes `main.run_agentic_rag` (sync `graph.invoke`) and post-processes thinking logs via `ExecutionStateCollector`.
- Other endpoints: health (`/health` → `main.rag_healthcheck`), feedback, Supabase stats, OnlyOffice doc serving.
- **thread_id**: `session_id` is passed as LangGraph `configurable.thread_id` for checkpointing and message persistence.
- **Checkpoint durability**: `CHECKPOINTER_TYPE` env controls backend (memory/sqlite/postgres). `CHECKPOINTER_DURABILITY` (defaults to `exit`) in `/chat/stream` saves only final state to reduce writes; synchronous path uses default graph behavior (per-node when checkpointer is present).

# 4) State Schema (RAGState or equivalent)
- **ParentState** (`Backend/models/parent_state.py`): shared orchestration fields—`session_id`, `user_query`, `original_question`, `selected_routers`, `workflow/task_type/doc_type/section_type`, `messages`, `conversation_history`, `data_sources`, routing flags, docgen outputs, desktop action plan, execution_trace (+ verbose).
- **DBRetrievalState** (`Backend/models/db_retrieval_state.py`): extends with RAG-specific artifacts—`query_plan`, `data_route`, `expanded_queries`, `retrieved_docs`/`graded_docs` (project/code/coop), `answer_citations`, `code/coop answers`, `follow_up_questions/suggestions`, image search fields, code verification fields (`pending_code_verification`, `approved_code_filenames`, etc.), `needs_fix`, `corrective_attempted`.
- **RAGState** (`Backend/models/rag_state.py`): extends DBRetrievalState with docgen + desktop metadata (`workflow`, `desktop_policy`, `task_type`, `doc_request`, `requires_desktop_action`, `desktop_action_plan/steps`, `doc_generation_result/warnings`, `output_artifact_ref`, `execution_trace` mirrors ParentState).
- Tracing fields: `execution_trace`/`execution_trace_verbose` are appended by `_wrap_node` in `graph/builder.py` for top-level nodes (`plan`, `doc_task_classifier`, `desktop_agent`). Subgraph nodes do not currently append to the trace.
- Message persistence: `messages` list is actively passed through streaming path (user message appended pre-graph, assistant message appended in `nodes/DBRetrieval/SQLdb/correct.py`). `conversation_history` is defined but not updated anywhere in current code (gap vs docs).

# 5) Graph Orchestration (LangGraph)
- Builder: `Backend/graph/builder.py` compiles a `StateGraph(ParentState)` with checkpointer injected.
- Nodes: `plan` (router selection), `doc_task_classifier` (docgen vs QA), `desktop_agent` (desktop/docgen subgraph), `db_retrieval` (DB subgraph), `router_dispatcher` (parallel routers).
- Edges/conditions:
  - Entry → `plan` → `doc_task_classifier`.
  - `doc_task_classifier` conditional `_doc_or_router`: if `workflow=='docgen'` or `task_type in {doc_section, doc_report}` → `desktop_agent`; elif `selected_routers` non-empty → `router_dispatcher`; else → `db_retrieval`.
  - `desktop_agent`/`router_dispatcher`/`db_retrieval` → END.
- **DBRetrieval subgraph** (`graph/subgraphs/db_retrieval_subgraph.py`, `StateGraph(DBRetrievalState)`):
  - Nodes: `rag_plan_router` (parallel `node_rag_plan` + `node_rag_router`), conditional to `generate_image_embeddings` (if `images_base64` & `use_image_similarity`) else `retrieve`; `image_similarity_search` → `retrieve`; `grade` → `answer` → `verify` → conditional `_verify_route` (fix → `retrieve`, ok → `correct`) → END.
  - Retries/loops: verification loop can route back to `retrieve` when `needs_fix`; image branch optional.
- **DesktopAgent subgraph** (`graph/subgraphs/desktop_agent_subgraph.py`, `StateGraph(ParentState)`):
  - `desktop_router` → conditional `_desktop_to_next` → `doc_generation` (if docgen workflow) → `finish` → END.
  - Docgen subgraph (`graph/subgraphs/document_generation_subgraph.py`, `StateGraph(RAGState)`): `doc_plan` → conditional to `doc_generate_section` or `doc_generate_report` → `doc_answer_adapter` → `doc_verify` (noop) → `doc_correct` (pass-through) → END.
- **Current graph diagram (ASCII):**
```
plan → doc_task_classifier → {desktop_agent | router_dispatcher | db_retrieval} → END

db_retrieval:
  rag_plan_router ─┬─> retrieve ─> grade ─> answer ─> verify ─┬─fix→ retrieve
                   │                                          └─ok→ correct → END
                   └─> generate_image_embeddings → image_similarity_search → retrieve

desktop_agent:
  desktop_router → {doc_generation | finish}
  doc_generation: doc_plan → {doc_generate_section|doc_generate_report}
                   → doc_answer_adapter → doc_verify → doc_correct → finish → END
```

# 6) Planner Behavior (As-Built)
- **Router selection planner**: `nodes/plan.py::node_plan` (Parent graph) prompts `router_selection_llm` with `ROUTER_SELECTION_PROMPT` to choose among `rag`, `web`, `desktop`. Defaults to `["rag"]` on parse failure. Emits stream_writer “thinking” event when available.
- **RAG plan**: `nodes/DBRetrieval/SQLdb/rag_plan.py::node_rag_plan` rewrites the *original question* using `RAG_PLANNER_PROMPT` (includes conversation context) and produces a normalized plan (reasoning + `steps` list). Extracts `project_filter` and seeds `expanded_queries`. This runs in parallel with the RAG router inside `rag_plan_router`.
- Complexity/intent heuristics: `_extract_complexity_from_reasoning` annotates `_planning_intelligence` (semantic telemetry stored on state for later logging).

# 7) Router Behavior (As-Built)
- **Doc vs QA**: `document_generation/document_classifier.py::node_doc_task_classifier` applies regex heuristics and optional `tier2.query_analyzer` to set `task_type` (`doc_section`/`doc_report` vs `qa`), `doc_type`, `section_type`, `workflow`, and `desktop_policy` (required/never).
- **Desktop router**: `nodes/DesktopAgent/desktop_router.py` runs `DESKTOP_ROUTER_PROMPT` to select `desktop_tools` (string list) when `"desktop"` is in `selected_routers`; otherwise no-op.
- **DB router**: `nodes/DBRetrieval/SQLdb/rag_router.py` classifies database usage across `project_db`, `code_db`, `coop_manual`, `speckle_db`; picks `project_route` (`smart` vs `large` chunks), auto-enables speckle for structural keywords, and enforces `project_db` when speckle is chosen. Stores `_routing_intelligence`.
- **Router dispatcher**: `nodes/router_dispatcher.py` runs selected routers in parallel (`rag` sync to propagate GraphInterrupt, `web`/`desktop` in ThreadPool). Merges sub-results into parent state.
- Ambiguity handling: `node_rag_router` defaults to `project_db` smart route if JSON parse fails; `node_plan` defaults to rag router on parse errors; no explicit clarification loop except `needs_clarification` flags (unused downstream in current code).

# 8) Retrieval / RAG (As-Built)
- **Plan executor**: `utils/plan_executor.py::execute_plan` executes plan steps (`RETRIEVE`), applying SQL prefilters (`create_sql_project_filter`) and hybrid retrievers per database. Uses Supabase vector stores (`supabase_client.py` → `vs_smart`, `vs_large`, `vs_code`, `vs_coop`) with RPC functions (`match_*`) and embedding model `emb`. MMR reranking functions (`mmr_rerank_supabase/code/coop`) applied.
- **Direct retrieval node**: `nodes/DBRetrieval/SQLdb/retrieve.py`:
  - If `query_plan` exists, runs `execute_plan`; else legacy hybrid retrieval with route-based chunk limits (`MAX_SMART_RETRIEVAL_DOCS`, `MAX_LARGE_RETRIEVAL_DOCS`).
  - Handles multi-db retrieval: project, code, coop; speckle placeholder via route.
  - **Human gate**: when `code_db` enabled, uses `langgraph.types.interrupt` to require approval (`code_verification`), and optionally `code_selection` for re-retrieval by filename; `GraphInterrupt` propagates to API.
  - Image branch: if `use_image_similarity`, calls `node_generate_image_description` / `node_image_similarity_search` before retrieval.
- **Grading**: `nodes/DBRetrieval/SQLdb/grade.py` caps docs (grader disabled by default `USE_GRADER=False`).
- **Synthesis**: `nodes/DBRetrieval/SQLdb/answer.py` synthesizes per enabled DB; in multi-db mode runs code/coop synthesis in background threads and project synthesis with streaming tokens via `get_stream_writer`. Applies dimension-based reranking and project-count heuristics.
- **Verification**: `nodes/DBRetrieval/SQLdb/verify.py` has `USE_VERIFIER=False` by default; when off, still generates follow-up Qs/Suggestions via `llm_verify` and doc index of graded docs.
- **Correction**: `nodes/DBRetrieval/SQLdb/correct.py` computes support score (disabled), preserves follow-ups, and appends assistant message to `messages` with sliding window (`MAX_CONVERSATION_HISTORY`). Intended conversation_history updates are absent (gap vs `MEMORY_FLOW_EXPLANATION.md`).
- **Context packaging**: Responses surface `final_answer`, `answer_citations`, `code/coop answers + citations`, `data_route`, `project_filter`, `image_similarity_results`, and follow-ups.

# 9) Desktop Agent / Tool Execution (As-Built)
- Desktop agent is minimal: `desktop_router` only selects tool names; no actual desktop tool execution nodes are implemented in the LangGraph path.
- Doc generation is the primary “desktop” action: `doc_generation` subgraph calls Tier2 generator/report drafter (`document_generation/{section_drafter.py,report_drafter.py}`) using Supabase or in-memory Qdrant vector store. `doc_plan` uses `tier2.query_analyzer` to build `doc_request` and flag `requires_desktop_action` when user mentions Word/save operations.
- `doc_answer_adapter` maps docgen output (`draft_text`/`combined_text`, `citations`) into `final_answer`/`answer_citations` so the same verify/correct tail can run.
- Think/act separation: not present; doc generation is a single LLM/tool call per node. No explicit deep-agent inner loop.
- File operations: OnlyOffice docx materialization in `api_server.py::materialize_onlyoffice_document` writes to `Backend/documents/` and serves via `/documents/{name}`. No sandboxing; direct filesystem writes.

# 10) Document Generation Subsystem (If Present)
- **Detection**: `node_doc_task_classifier` (heuristics + optional QueryAnalyzer) flips `workflow` to `docgen`, sets `task_type`, `doc_type`, `section_type`, and forces `desktop_policy="required"`.
- **Execution**: DesktopAgent subgraph routes to `doc_generation` → `doc_plan` (builds `doc_request`, desktop_action_plan) → `doc_generate_section` or `doc_generate_report` (Tier2 generator/drafter) → `doc_answer_adapter` → verify/correct pass-through.
- **Outputs**: `doc_generation_result` carries `draft_text`/`sections`, `citations`, `warnings`. CSV logging for docgen runs in `main.py` via `utils.csv_logger.append_draft_csv` (default path `Local Agent/info_retrieval/data/drafted_sections.csv`).
- **UI integration**: API attaches `doc_generation_result`/`warnings` plus optional OnlyOffice `document_state` when `should_materialize_doc` detects doc workflows.

# 11) Observability / Tracing / Logging
- Logging setup: `Backend/config/logging_config.py` configures component loggers (`QUERY_FLOW`, `ROUTING`, `ENHANCEMENT`, etc.) with DEBUG_MODE-based verbosity.
- Execution trace: `_wrap_node` in `graph/builder.py` appends node names and a verbose entry (task_type/workflow/desktop flags) to `execution_trace` and `execution_trace_verbose` for top-level nodes only.
- Streaming thinking logs: `/chat/stream` uses `thinking/intelligent_log_generator.py` to turn node updates into user-facing “thinking” events (plan/router/retrieve/grade/answer/verify/correct, image stages). Token streaming leverages LangGraph `messages` mode.
- Non-stream path: `thinking/rag_wrapper.py` collects execution state and uses `LLMThinkingGenerator` to generate markdown thinking logs returned in `ChatResponse.thinking_log`.
- Supabase logging: `helpers/supabase_logger` (if available) logs user query, combined responses, citations count, latency, and uploads images.
- CSV logging: docgen drafts logged via `append_draft_csv` in `main.py`.
- Errors/warnings: logging throughout nodes; verification disabled by default, so fewer warnings. No centralized tracing store.
- Example trace (top-level): for a docgen request → `execution_trace = ["plan", "doc_task_classifier", "desktop_agent"]`; for QA → `["plan", "doc_task_classifier", "db_retrieval"]` (sub-nodes are not recorded).

# 12) Human-in-the-Loop / Interrupts (As-Built or Missing)
- Implemented: code verification gate in `nodes/DBRetrieval/SQLdb/retrieve.py` via `langgraph.types.interrupt`/`GraphInterrupt`. Prompts user to approve/reject code references and optionally select specific codes; resumes retrieval accordingly.
- Not found: other approval/confirm-before-edit gates, pause/resume checkpoints, or explicit human interrupts in docgen/desktop paths. No verifier-driven human confirmation.
- Best insertion points:
  - Docgen quality gate after `doc_answer_adapter` (before `doc_verify`) to allow human edits or approval.
  - Desktop router/tool selection to require confirmation before executing OS actions (once implemented).
  - Retrieval follow-up when `needs_clarification` is set in router results.

# 13) Persistence Model (State vs Disk vs Store vs DB)
- **LangGraph checkpointing**: `Backend/graph/checkpointer.py` supports `memory` (default, non-persistent), `sqlite` (file), `postgres/supabase` (async). `/chat/stream` can reduce writes via `CHECKPOINTER_DURABILITY=exit`.
- **State stored**: `messages` (actively), execution traces, docgen outputs, retrieval artifacts per state. `conversation_history` field exists but is not updated in code (gap).
- **Supabase vector stores**: `vs_smart`, `vs_large`, `vs_code`, `vs_coop` tables configured via env (`SUPA_*` vars) and accessed for retrieval.
- **Filesystem**: OnlyOffice docs rendered under `Backend/documents/`; CSV drafts under `Local Agent/info_retrieval/data/drafted_sections.csv` (default).
- **SESSION_MEMORY/FOCUS_STATES** (`models/memory.py`): in-memory Python dict for semantic context and backward compatibility; not durable across restarts.
- No explicit `/workspace` vs `/memories` separation; no long-term durable memory beyond optional checkpointer DB.

# 14) Gaps vs Target Architecture (Most Important)
| Target Stage | Current Implementation | Gap |
| --- | --- | --- |
| Planner | Router selector (`node_plan`) + RAG planner (`node_rag_plan`), both LLM-based. | Two planners overlap; router selector doesn’t feed structured plan to downstream routers; sync path doesn’t append user message before invoke. |
| Router | Doc/QA classifier (`node_doc_task_classifier`), DB router (`node_rag_router`), router_dispatcher for multi-router. | No explicit “router” node selecting between docgen vs retrieval vs desktop in one place; `selected_routers` seldom used beyond rag; no clarification loop when ambiguous. |
| Retrieval (RAG) | DB subgraph with plan/router → retrieve → grade → answer → verify → correct; Supabase vector stores; code verification interrupt. | Verifier disabled; grading disabled; execution_trace not capturing subgraph steps; conversation_history not persisted; cache/eviction not present; retries only via verify loop. |
| DesktopAgent (Deep Agent) | Desktop router + docgen subgraph; Tier2 doc generation; optional desktop_action_plan metadata. | No desktop tool execution or deep-agent loop; no tool gating except code verification (not desktop); no summarization/eviction of tool outputs; no human approval. |
| Verifier | `node_verify` exists but `USE_VERIFIER=False`; follow-up Q generation only. | No active verifier loop, no retries driven by verification, no human gate. |

# 15) Recommendations (Prioritized Refactor Plan)
1. **Persist conversation history properly** (add/update in `nodes/DBRetrieval/SQLdb/correct.py` and reuse in `main.py` sync path) to align with `MEMORY_FLOW_EXPLANATION` and improve follow-up quality; risk: low; complexity: medium.
2. **Unify planner/router outputs** (make `node_plan` emit structured workflow + router choice feeding `_doc_or_router` and `selected_routers`; consolidate with `node_rag_plan` outputs) to reduce redundant LLM calls; risk: medium; complexity: medium.
3. **Enable/repair verifier loop** (toggle `USE_VERIFIER`, ensure `_verify_route` triggers retries with guardrails) so `verify` meaningfully controls fix/accept; risk: medium; complexity: medium.
4. **Extend execution_trace to subgraphs** (wrap DB retrieval and docgen nodes) for observability and UI node_path accuracy; risk: low; complexity: medium.
5. **Add human gate for docgen/desktop actions** (interrupt after `doc_answer_adapter` or before desktop actions) to mirror code verification safety; risk: medium; complexity: medium.
6. **Implement desktop tool actions or stub Deep Agent loop** (inside `desktop_agent` subgraph, add tool-calling node with retry/summary) to realize DesktopAgent stage; risk: medium; complexity: large.
7. **Re-enable grading with limits** (`node_grade.USE_GRADER=True` with bounded tokens) or add lightweight heuristic filter to improve citation quality; risk: medium; complexity: small.
8. **Clarification branch when router is unsure** (use `needs_clarification` to interrupt/ask user) to prevent misroutes; risk: low; complexity: medium.
9. **Normalize persistence** (default to sqlite/postgres checkpointer in env, align `/chat` path to append user message like streaming path) to avoid divergence between sync/async flows; risk: low; complexity: small.
10. **Add eviction/summarization for large tool outputs** (e.g., summarize image search results or docgen debug fields before persisting to state) to keep checkpoint storage manageable; risk: low; complexity: medium.
