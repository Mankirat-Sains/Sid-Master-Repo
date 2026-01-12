# DocGeneration LangGraph Branch

Nodes:
- `node_doc_task_classifier`: Heuristically tags queries as `doc_section` / `doc_report` vs `qa` and seeds doc_type/section_type hints.
- `node_doc_plan`: Runs Tier2 `QueryAnalyzer`, builds `doc_request`, flags `requires_desktop_action` and `desktop_action_plan`.
- `node_desktop_execute`: Execution-only hook for Desktop Agent when doc actions are requested; never alters routing.
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
     -> if task_type in {doc_section, doc_report}:
           doc_plan -> desktop_execute -> doc_generate_(section|report)
           -> doc_answer_adapter -> verify -> correct -> END
        else:
           router_dispatcher|rag -> retrieve -> grade -> answer -> verify -> correct -> END
```

Desktop Agent:
- This branch keeps Desktop Agent execution-only. `node_desktop_execute` is the single hook to call out for open/save actions when requested.
