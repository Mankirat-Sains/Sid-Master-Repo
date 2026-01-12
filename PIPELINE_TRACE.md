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
- Nodes registered (wrap logs task_type/desktop flags):
  - plan → doc_task_classifier → doc_plan → desktop_router → doc_think → doc_act → doc_generate_section|doc_generate_report → doc_answer_adapter → verify → correct
  - router_dispatcher, rag, generate_image_embeddings, image_similarity_search, retrieve, grade, answer, verify, correct
- Entry point: `plan`.

### Routing Conditions
- plan → doc_task_classifier (always).
- doc_task_classifier → `_doc_or_router`:
  - If `workflow == "docgen"` or `task_type in {doc_section, doc_report}` → `doc_plan`.
  - Else → router path (`router_dispatcher` if routers selected, else `rag`).
- doc_act → `_doc_generate_route`: doc_report → doc_generate_report else doc_generate_section.
- verify → `_verify_route`: fix → retrieve, ok → correct.
- router_dispatcher/rag → optional image branch → retrieve → grade → answer → verify → correct.

## Doc Generation Flow (task_type=doc_section/doc_report or workflow=docgen)
1) doc_task_classifier: sets `workflow="docgen"`, `desktop_policy="required"`, task_type/doc_type/section_type hints.
2) doc_plan: runs Tier2 QueryAnalyzer; builds `doc_request`; sets `requires_desktop_action`; passes `desktop_action_plan`.
3) desktop_router: routes to desktop tool (Word default for docgen).
4) doc_think: shapes execution steps (no decisions).
5) doc_act: executes steps (noop allowed).
6) doc_generate_section or doc_generate_report: Tier2 generation.
7) doc_answer_adapter: sets `final_answer`/`answer` and `answer_citations`; passes warnings.
8) verify → correct tail unchanged.

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
  doc_task_classifier → doc_plan → desktop_router → doc_think → doc_act → doc_generate_report → doc_answer_adapter → verify → correct.
- Prompt “What does the report say about expansion joints?”:
  doc_task_classifier → rag → retrieve → grade → answer → verify → correct.
