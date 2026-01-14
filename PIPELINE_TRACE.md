# PIPELINE_TRACE.md

## UI → Backend
- Web UI calls FastAPI endpoint: `POST /chat` (Backend/api_server.py).
- Handler: `chat` in `api_server.py` calls `thinking.rag_wrapper.run_agentic_rag_with_thinking_logs`, which delegates to `Backend/main.py:run_agentic_rag`.

## Backend Entrypoint
- `run_agentic_rag(question, session_id, data_sources, images_base64)` (Backend/main.py)
  - Builds `RAGState` with `user_query=question`.
  - Invokes LangGraph via `graph.invoke(asdict(init), config={"configurable": {"thread_id": session_id}})`.
  - Logs route summary: workflow, task_type, branch, desktop_policy.
  - Returns `final_state.final_answer` (or multi-DB variants), citations, etc., to the API handler.

## LangGraph Registration (Backend/graph/builder.py)
- Nodes registered (with execution tracing):
  - plan → doc_task_classifier → desktop_agent subgraph | router_dispatcher | db_retrieval subgraph
  - db_retrieval subgraph: rag_plan_router → generate_image_embeddings? → retrieve → grade → answer → verify → correct
- Entry point: `plan`.

### Routing Conditions
- plan → doc_task_classifier (always).
- doc_task_classifier → `_doc_or_router`:
  - If `workflow == "docgen"` or `task_type in {doc_section, doc_report}` → `desktop_agent` subgraph.
  - Else → router path (`router_dispatcher` if routers selected, else `db_retrieval`).
- router_dispatcher/db_retrieval → optional image branch → retrieve → grade → answer → verify → correct.

## Doc Generation Flow (task_type=doc_section/doc_report or workflow=docgen)
1) doc_task_classifier: sets `workflow="docgen"`, `desktop_policy="required"`, task_type/doc_type/section_type hints.
2) desktop_agent subgraph (Backend/graph/subgraphs/desktop_agent_subgraph.py):
   - desktop_router runs when `"desktop"` is in `selected_routers`.
   - document_generation_subgraph: doc_entry → doc_retrieve (guard) → doc_plan (Tier2 QueryAnalyzer) → doc_generate_section|doc_generate_report → doc_answer_adapter → doc_verify → doc_correct.
3) doc_answer_adapter: sets `final_answer`/`answer_citations`; passes warnings; verify/correct tail mirrors QA branch.

## QA Flow (default)
- doc_task_classifier → router_dispatcher|rag → (optional image) → retrieve → grade → answer → verify → correct.

## State Fields Used for Routing
- `workflow` ("qa" | "docgen")
- `task_type` ("qa" | "doc_section" | "doc_report")
- `desktop_policy` ("required" | "optional" | "never")
- `doc_type`, `section_type`, `requires_desktop_action`, `desktop_action_plan`
- Image flags: `images_base64`, `use_image_similarity`

## Mismatches / Notes
- Web UI `/chat` already goes through `run_agentic_rag`, which invokes LangGraph. No bypass detected.
- Desktop steps now always run in docgen branch (even if noop), as per builder wiring.
- Final answer returned to UI is `final_answer` (with `answer` mirrored in doc_answer_adapter).

## Example Branching
- Prompt “Create an RP report doc …”:
  doc_task_classifier → desktop_agent → doc_plan → doc_generate_report → doc_answer_adapter → verify → correct.
- Prompt “What does the report say about expansion joints?”:
  doc_task_classifier → db_retrieval → retrieve → grade → answer → verify → correct.
