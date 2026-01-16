# DocGen branch (under DesktopAgent)

Nodes:
- `task_classifier`: Heuristically tags queries as `doc_section` / `doc_report` vs `qa` and seeds doc_type/section_type hints. Also sets `workflow`/`desktop_policy`.
- `plan`: Runs Tier2 `QueryAnalyzer`, builds `doc_request`, flags `requires_desktop_action`, and prepares a `desktop_action_plan` when needed.
- `section_generator`: Calls `Tier2Generator` to draft a single section; stores `doc_generation_result` and warnings.
- `report_generator`: Calls `ReportDrafter` for multi-section reports; stores `doc_generation_result`.
- `answer_adapter`: Converts doc generation output to `final_answer`/`answer_citations` so downstream nodes can read the draft.

State fields used:
- `task_type`, `doc_type`, `section_type`, `doc_request`
- `requires_desktop_action`, `desktop_action_plan`, `output_artifact_ref`
- `doc_generation_result`, `doc_generation_warnings`
- `execution_trace`, `execution_trace_verbose`

Routing:
```
plan
  -> doc_task_classifier
     -> if workflow/doc task: desktop_agent (dispatches to docgen_subgraph)
        -> doc_plan -> doc_generate_(section|report) -> doc_answer_adapter -> END
     -> else:
        router_dispatcher|db_retrieval (handled inside subgraphs) -> END
```

Desktop Agent:
- Desktop execution is handled inside the `desktop_agent_subgraph`, which invokes the doc generation subgraph when doc tasks are detected. No inline desktop nodes live in the parent graph.
