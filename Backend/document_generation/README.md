# Document Generation Workflow

This package houses all document-generation components used by the orchestrator.
Modules map directly to the LangGraph nodes and subgraphs:

- `document_classifier.classify_document_task` (alias `node_doc_task_classifier`): detects doc intent, seeds `doc_type`/`section_type`, and sets `workflow`/`desktop_policy`.
- `document_planner.build_document_plan` (alias `node_doc_plan`): runs Tier2 `QueryAnalyzer`, builds `doc_request`, and flags desktop needs (`requires_desktop_action`, `desktop_action_plan`).
- `section_drafter.draft_section` / `report_drafter.draft_report` (aliases `node_doc_generate_section` / `node_doc_generate_report`): call Tier2 generators and return `doc_generation_result` + warnings.
- `answer_adapter.adapt_generation_output` (alias `node_doc_answer_adapter`): maps generation output into `final_answer`/`answer_citations`.
- `desktop_actions.*`: minimal placeholders for desktop action planning/execution (kept for compatibility; deep desktop tools live under `desktop_agent/tools`).

State fields consumed/produced:
- `task_type`, `doc_type`, `section_type`, `doc_request`
- `requires_desktop_action`, `desktop_action_plan`, `desktop_steps`, `output_artifact_ref`
- `doc_generation_result`, `doc_generation_warnings`, `answer_citations`
- `execution_trace`, `execution_trace_verbose`

Routing overview:
```
plan
  -> doc_task_classifier
     -> desktop_agent_subgraph
         -> desktop_router (selected routers only)
         -> document_generation_subgraph
              doc_entry -> doc_retrieve (guard) -> doc_plan
              -> doc_generate_section|doc_generate_report
              -> doc_answer_adapter -> doc_verify -> doc_correct -> END
     -> else: router_dispatcher|db_retrieval subgraph paths
```

Location notes:
- Subgraph wiring lives in `Backend/graph/subgraphs/document_generation_subgraph.py`.
- Deep desktop loop wraps generation via `desktop_agent/tools/document_generation_tool.py`.
