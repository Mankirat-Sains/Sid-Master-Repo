# DocGeneration LangGraph Branch

Nodes:
- `node_doc_task_classifier`: Heuristically tags queries as `doc_section` / `doc_report` vs `qa` and seeds doc_type/section_type hints.
- `node_doc_plan`: Runs Tier2 `QueryAnalyzer`, builds `doc_request`, flags `requires_desktop_action` and `desktop_action_plan`.
- `node_desktop_router`: Desktop routing (existing node) used in the docgen branch before execution.
- `node_doc_think`: Shapes execution steps from the plan (execution-only).
- `node_doc_act`: Executes steps (noop if none); keeps execution-only semantics.
- `node_doc_generate_section`: Calls Tier2Generator to draft a single section; stores `doc_generation_result` and warnings.
- `node_doc_generate_report`: Calls ReportDrafter for multi-section reports; stores `doc_generation_result`.
- `node_doc_answer_adapter`: Converts doc generation output to `final_answer`/`answer_citations` so verify/correct can run unchanged.

State fields used:
- `task_type`, `doc_type`, `section_type`, `doc_request`
- `requires_desktop_action`, `desktop_action_plan`, `output_artifact_ref`
- `doc_generation_result`, `doc_generation_warnings`

Routing:
```
plan
  -> doc_task_classifier
     -> if workflow=docgen:
           doc_plan -> desktop_router -> doc_think -> doc_act -> doc_generate_(section|report)
           -> doc_answer_adapter -> verify -> correct -> END
        else:
           router_dispatcher|rag -> retrieve -> grade -> answer -> verify -> correct -> END
```

Desktop Agent:
- This branch keeps Desktop Agent execution-only. doc_think/doc_act are the hooks to call out for open/save actions when requested.
