"""
Deep desktop agent loop implementing think-act-observe cycles.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.errors import GraphInterrupt

from models.rag_state import RAGState
from persistence.workspace_manager import get_workspace_manager
from nodes.DesktopAgent.tools.docgen_tool import get_docgen_tool
from nodes.DesktopAgent.tools.doc_edit_tool import get_doc_edit_tool
from utils.tool_eviction import get_evictor
from config.settings import (
    MAX_DEEP_AGENT_ITERATIONS,
    INTERRUPT_DESTRUCTIVE_ACTIONS,
)
from config.llm_instances import llm_fast

logger = logging.getLogger(__name__)


def _get(state: Any, key: str, default: Any = None) -> Any:
    """Safe getter for dataclass or dict state."""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


class DeepDesktopLoop:
    """Deep agent that executes desktop tasks through iterative think-act-observe cycles."""

    def __init__(self) -> None:
        self.max_iterations = MAX_DEEP_AGENT_ITERATIONS
        self.workspace_mgr = get_workspace_manager()
        self.docgen_tool = get_docgen_tool()
        self.doc_edit_tool = get_doc_edit_tool()
        self.evictor = get_evictor()
        # Use raw llm_fast to avoid passing unsupported stream_options to legacy OpenAI clients
        self.planner_llm = llm_fast
        self.executor_llm = llm_fast
        self.tools = self._initialize_tools()
        logger.info(f"DeepDesktopLoop initialized with max {self.max_iterations} iterations")

    def run(self, state: RAGState) -> Dict[str, Any]:
        """Main execution entry point."""
        try:
            thread_id = _get(state, "session_id") or _get(state, "thread_id") or "default"
            workspace_dir = self.workspace_mgr.get_thread_workspace(thread_id)
            logger.info(f"Desktop loop starting for thread {thread_id} in {workspace_dir}")

            plan = self._create_plan(state, workspace_dir)
            plan_updates = plan.get("state_updates", {}) if isinstance(plan, dict) else {}
            if not plan or not plan.get("steps"):
                logger.warning("No plan generated, returning early")
                return {
                    "desktop_loop_result": {"status": "no_plan", "message": "Could not create execution plan"},
                    "requires_desktop_action": False,
                }

            results = self._execute_plan(plan, state, workspace_dir, thread_id)
            final_result = self._package_results(results, workspace_dir, plan)

            # Extract docgen output (if any) to propagate to parent graph/API
            docgen_result = None
            docgen_warnings: List[str] = []
            plan_warns: List[str] = []
            if isinstance(plan_updates, dict) and plan_updates.get("doc_generation_warnings"):
                plan_warns = list(plan_updates.get("doc_generation_warnings") or [])
                plan_updates = {k: v for k, v in plan_updates.items() if k != "doc_generation_warnings"}
            for r in results:
                action_res = r.get("action", {}) or {}
                if action_res.get("action") == "generate_document" and action_res.get("success"):
                    docgen_result = action_res.get("doc_generation_result")
                    if not docgen_result:
                        output_text = action_res.get("output", "")
                        docgen_result = {
                            "draft_text": output_text,
                            "warnings": action_res.get("warnings", []),
                            "citations": action_res.get("citations", []),
                            "metadata": action_res.get("metadata", {}),
                        }
                    if isinstance(docgen_result, dict):
                        docgen_warnings = docgen_result.get("warnings", []) or []
                    break

            return {
                "desktop_loop_result": final_result,
                "desktop_plan_steps": plan.get("steps", []),
                "desktop_iteration_count": len(results),
                "desktop_workspace_dir": str(workspace_dir),
                "desktop_workspace_files": [str(f.relative_to(workspace_dir)) for f in workspace_dir.iterdir() if f.is_file()],
                "tool_execution_log": [r.get("action", {}) for r in results],
                "requires_desktop_action": False,
                "output_artifact_ref": final_result.get("artifact_ref"),
                "doc_generation_result": docgen_result,
                "doc_generation_warnings": plan_warns + (docgen_warnings or []),
                "final_answer": (docgen_result or {}).get("draft_text") if isinstance(docgen_result, dict) else None,
                **(plan_updates or {}),
            }
        except GraphInterrupt:
            logger.info("Propagating GraphInterrupt from deep desktop loop.")
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Error in deep desktop loop: {exc}", exc_info=True)
            return {
                "desktop_loop_result": {"status": "error", "error": str(exc)},
                "requires_desktop_action": False,
            }

    def _initialize_tools(self) -> List[str]:
        """Initialize tool set for desktop operations."""
        return [
            "read_file",
            "write_file",
            "edit_file",
            "delete_file",
            "list_files",
            "generate_document",
            "edit_document",
        ]

    def _create_plan(self, state: RAGState, workspace_dir: Path) -> Dict[str, Any]:
        """Create execution plan from user request."""
        user_query = _get(state, "user_query", "")
        desktop_action_plan = _get(state, "desktop_action_plan", {}) or {}
        task_type = desktop_action_plan.get("task_type", "unknown")

        # For docgen workflows, short-circuit to a deterministic plan that actually calls docgen.
        is_doc_workflow = _get(state, "workflow") == "docgen" or str(_get(state, "task_type")).startswith("doc_")
        if is_doc_workflow:
            doc_plan_updates: Dict[str, Any] = {}
            try:
                from nodes.DesktopAgent.doc_generation.plan import build_doc_plan

                doc_plan_updates = build_doc_plan(state)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"DOCGEN: doc plan helper failed in deep loop: {exc}")
                doc_plan_updates = {}

            doc_request = doc_plan_updates.get("doc_request") or _get(state, "doc_request", {}) or {}
            if user_query and not doc_request.get("user_query"):
                doc_request["user_query"] = user_query
            doc_type = _get(state, "doc_type")
            section_type = _get(state, "section_type")
            if doc_type:
                doc_request.setdefault("doc_type", doc_type)
            if section_type:
                doc_request.setdefault("section_type", section_type)
            section_queue = doc_plan_updates.get("section_queue") or _get(state, "section_queue", []) or []
            approved_sections = doc_plan_updates.get("approved_sections") or _get(state, "approved_sections", []) or []
            template_id = doc_plan_updates.get("template_id") or _get(state, "template_id")
            doc_type_variant = doc_plan_updates.get("doc_type_variant") or _get(state, "doc_type_variant")
            current_section_id = doc_plan_updates.get("current_section_id") or doc_request.get("section_id")
            if section_queue and not doc_request.get("section_queue"):
                doc_request["section_queue"] = section_queue
            if approved_sections and not doc_request.get("approved_sections"):
                doc_request["approved_sections"] = approved_sections
            if template_id and not doc_request.get("template_id"):
                doc_request["template_id"] = template_id
            if doc_type_variant and not doc_request.get("doc_type_variant"):
                doc_request["doc_type_variant"] = doc_type_variant
            if current_section_id:
                doc_request.setdefault("section_id", current_section_id)
            logger.info("Doc workflow detected; forcing generate_document plan")
            return {
                "goal": f"Generate document content for: {user_query or 'document request'}",
                "steps": [
                    {
                        "action": "generate_document",
                        "reasoning": "Doc workflow requires generating draft content via docgen.",
                        "params": {"doc_request": doc_request},
                    }
                ],
                "state_updates": {
                    **doc_plan_updates,
                    "doc_request": doc_request,
                    "section_queue": section_queue,
                    "approved_sections": approved_sections,
                    "template_id": template_id,
                    "doc_type_variant": doc_type_variant,
                    "current_section_id": current_section_id,
                },
            }

        planning_prompt = f"""You are a desktop task planner. Break down the following request into concrete steps.

User Request: {user_query}
Task Type: {task_type}

Available tools:
- read_file: Read a file from workspace
- write_file: Write content to a file
- list_files: List files in workspace
- generate_document: Generate document content (calls docgen)
- edit_document: Apply structured DOCX ops (insert/replace/delete/style/reorder) via doc agent

Create a step-by-step plan. Each step should specify:
- action: The tool to use
- reasoning: Why this step is needed
- params: Parameters for the tool

Respond in JSON format:
{{
    "goal": "Brief description of overall goal",
    "steps": [
        {{
            "action": "tool_name",
            "reasoning": "Why this step",
            "params": {{"param": "value"}}
        }}
    ]
}}

Keep plans concise (3-7 steps max).
"""

        try:
            messages = [
                SystemMessage(content="You are a precise task planner. Output valid JSON only."),
                HumanMessage(content=planning_prompt),
            ]
            response = self.planner_llm.invoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            if "```json" in response_text:
                response_text = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```", 1)[1].split("```", 1)[0].strip()
            plan = json.loads(response_text)
            logger.info(f"Created plan with {len(plan.get('steps', []))} steps: {plan.get('goal', 'N/A')}")
            return plan
        except Exception as exc:
            logger.error(f"Error creating plan: {exc}", exc_info=True)
            # Fallback: single-step plan favoring doc generation for doc workflows
            preferred_action = "generate_document"
            if not (str(task_type).startswith("doc_") or _get(state, "workflow") == "docgen"):
                preferred_action = "write_file"
            return {
                "goal": f"Execute {task_type} task",
                "steps": [
                    {
                        "action": preferred_action,
                        "reasoning": "Fallback single-step execution",
                        "params": {"content": user_query},
                    }
                ],
                "fallback": True,
            }

    def _execute_plan(
        self,
        plan: Dict[str, Any],
        state: RAGState,
        workspace_dir: Path,
        thread_id: str,
    ) -> List[Dict[str, Any]]:
        """Execute plan steps with think-act-observe cycles."""
        steps = plan.get("steps", [])
        results: List[Dict[str, Any]] = []

        for step_idx, step in enumerate(steps):
            if step_idx >= self.max_iterations:
                logger.warning(f"Hit max iterations ({self.max_iterations}), stopping")
                break

            if "action_id" not in step:
                step["action_id"] = f"{step.get('action', 'unknown')}_{step_idx}_{uuid4().hex[:8]}"

            logger.info(f"Executing step {step_idx + 1}/{len(steps)}: {step.get('action')}")
            try:
                thought = self._think_about_step(step, state, results, workspace_dir)
                action_result = self._execute_step(step, thought, workspace_dir, thread_id, state)
                observation = self._observe_result(action_result, step, workspace_dir)

                iteration_result = {
                    "step_index": step_idx,
                    "step": step,
                    "thought": thought,
                    "action": action_result,
                    "observation": observation,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                results.append(iteration_result)

                if observation.get("is_complete", False):
                    logger.info(f"Task completed at step {step_idx + 1}")
                    break
                if observation.get("has_error", False) and observation.get("is_critical", False):
                    logger.error(f"Critical error at step {step_idx + 1}: {observation.get('error')}")
                    break
            except GraphInterrupt:
                logger.info(f"Interrupt raised at step {step_idx + 1}")
                raise

        return results

    def _think_about_step(
        self,
        step: Dict[str, Any],
        state: RAGState,
        previous_results: List[Dict[str, Any]],
        workspace_dir: Path,
    ) -> Dict[str, Any]:
        """Reason about the current step before execution."""
        previous_summary: List[str] = []
        for r in previous_results[-3:]:
            obs = r.get("observation", {})
            previous_summary.append(
                f"Step {r['step_index']}: {r['step'].get('action')} -> {obs.get('summary', 'completed')}"
            )

        workspace_snapshot = self.workspace_mgr.get_workspace_snapshot(_get(state, "session_id", "default"))

        thought = {
            "step_action": step.get("action"),
            "step_reasoning": step.get("reasoning", ""),
            "previous_context": "\n".join(previous_summary) if previous_summary else "First step",
            "workspace_files": workspace_snapshot.get("files", []),
            "analysis": f"Preparing to {step.get('action')} with params {step.get('params', {})}",
        }
        logger.debug(f"Thought: {thought['analysis']}")
        return thought

    def _execute_step(
        self,
        step: Dict[str, Any],
        thought: Dict[str, Any],
        workspace_dir: Path,
        thread_id: str,
        state: Optional[RAGState] = None,
    ) -> Dict[str, Any]:
        """Execute a single step with interrupt gates for destructive actions."""
        action = step.get("action", "unknown")
        params = step.get("params", {}) or {}

        action_id = step.get("action_id") or f"{action}_{hash(json.dumps(params, sort_keys=True))}"

        if INTERRUPT_DESTRUCTIVE_ACTIONS and self._is_destructive_action(action):
            approved_actions = _get(state, "desktop_approved_actions", []) if state is not None else []
            if action_id not in approved_actions:
                interrupt_data = self._create_interrupt_data(
                    action=action,
                    params=params,
                    step=step,
                    thought=thought,
                    workspace_dir=workspace_dir,
                    action_id=action_id,
                )
                logger.info(f"Raising interrupt for destructive action: {action}")
                gi = GraphInterrupt(f"Approval required for {action}")
                gi.data = interrupt_data
                raise gi

        try:
            if action == "read_file":
                result = self._tool_read_file(params, workspace_dir, thread_id)
            elif action == "write_file":
                result = self._tool_write_file(params, workspace_dir, thread_id)
            elif action == "edit_file":
                result = self._tool_edit_file(params, workspace_dir, thread_id)
            elif action == "delete_file":
                result = self._tool_delete_file(params, workspace_dir, thread_id)
            elif action == "list_files":
                result = self._tool_list_files(params, workspace_dir, thread_id)
            elif action == "generate_document":
                result = self._tool_generate_document(params, workspace_dir, thread_id, state)
            elif action == "edit_document":
                result = self._tool_edit_document(params, workspace_dir, thread_id)
            else:
                result = {"success": False, "error": f"Unknown action: {action}", "action": action}

            result["action"] = action
            result["action_id"] = action_id
            result["timestamp"] = datetime.utcnow().isoformat()
            return result
        except GraphInterrupt:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Error executing {action}: {exc}", exc_info=True)
            return {
                "success": False,
                "error": str(exc),
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _observe_result(
        self,
        action_result: Dict[str, Any],
        step: Dict[str, Any],
        workspace_dir: Path,
    ) -> Dict[str, Any]:
        """Observe and interpret action result."""
        success = action_result.get("success", False)
        action = action_result.get("action", "unknown")

        observation: Dict[str, Any] = {
            "success": success,
            "action": action,
            "summary": "",
            "is_complete": False,
            "has_error": not success,
            "is_critical": False,
        }

        if success:
            if action == "generate_document":
                observation["summary"] = "Document generated successfully"
                observation["is_complete"] = True
            elif action == "edit_document":
                observation["summary"] = "Document edited successfully"
            elif action == "write_file":
                observation["summary"] = f"Wrote {action_result.get('filename', 'file')}"
            elif action == "read_file":
                observation["summary"] = f"Read {len(action_result.get('content', ''))} chars from file"
            else:
                observation["summary"] = f"Completed {action}"
        else:
            error = action_result.get("error", "Unknown error")
            observation["summary"] = f"Failed: {error}"
            observation["error"] = error
            if "not found" in error.lower() or "permission" in error.lower():
                observation["is_critical"] = True

        logger.info(f"Observation: {observation['summary']}")
        return observation

    def _is_destructive_action(self, action: str) -> bool:
        """Check if an action is destructive and requires approval."""
        destructive_actions = {
            "write_file",
            "edit_file",
            "edit_document",
            "delete_file",
            "execute_code",
            "materialize_doc",
        }
        return action in destructive_actions

    def _create_interrupt_data(
        self,
        action: str,
        params: Dict[str, Any],
        step: Dict[str, Any],
        thought: Dict[str, Any],
        workspace_dir: Path,
        action_id: str,
    ) -> Dict[str, Any]:
        """Create detailed interrupt data for user approval."""
        workspace_snapshot = self.workspace_mgr.get_workspace_snapshot(workspace_dir.name)

        interrupt_data: Dict[str, Any] = {
            "action_id": action_id,
            "action": action,
            "params": params,
            "reasoning": step.get("reasoning", "No reasoning provided"),
            "thought_analysis": thought.get("analysis", ""),
            "workspace_context": {
                "existing_files": workspace_snapshot.get("files", []),
                "file_count": workspace_snapshot.get("file_count", 0),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        if action == "write_file":
            filename = params.get("filename", params.get("file", "unknown"))
            content_preview = params.get("content", "")[:500]
            file_exists = (workspace_dir / filename).exists()
            interrupt_data["action_context"] = {
                "filename": filename,
                "file_exists": file_exists,
                "will_overwrite": file_exists,
                "content_preview": content_preview,
                "content_size": len(params.get("content", "")),
            }
        elif action == "edit_file":
            filename = params.get("filename", params.get("file", "unknown"))
            interrupt_data["action_context"] = {
                "filename": filename,
                "edit_type": params.get("edit_type", "unknown"),
                "changes_preview": str(params.get("changes", ""))[:500],
            }
        elif action == "delete_file":
            filename = params.get("filename", params.get("file", "unknown"))
            file_path = workspace_dir / filename
            interrupt_data["action_context"] = {
                "filename": filename,
                "file_exists": file_path.exists(),
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
            }

        return interrupt_data

    def _package_results(
        self,
        results: List[Dict[str, Any]],
        workspace_dir: Path,
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Package execution results into final output."""
        all_success = all(r.get("observation", {}).get("success", False) for r in results) if results else False

        final_output = None
        for r in reversed(results):
            if r.get("observation", {}).get("success"):
                action_result = r.get("action", {})
                if action_result.get("output"):
                    final_output = action_result["output"]
                    break

        artifact_ref = None
        if final_output:
            output_file = workspace_dir / f"output_{uuid4().hex[:8]}.md"
            output_file.write_text(final_output, encoding="utf-8")
            artifact_ref = {"type": "file", "path": str(output_file), "size": len(final_output)}

        return {
            "status": "success" if all_success else "partial",
            "goal": plan.get("goal", "Unknown"),
            "steps_executed": len(results),
            "steps_planned": len(plan.get("steps", [])),
            "final_output": final_output[:1000] if final_output else None,
            "artifact_ref": artifact_ref,
            "workspace_path": str(workspace_dir),
            "execution_summary": [
                {
                    "step": r["step"].get("action"),
                    "success": r.get("observation", {}).get("success"),
                    "summary": r.get("observation", {}).get("summary"),
                }
                for r in results
            ],
        }

    # Interrupt handling pattern documentation:
    # When a destructive action is detected, this loop raises GraphInterrupt with detailed context.
    # The interrupt pauses execution; to resume:
    # 1) User approves action (e.g., via API) and adds action_id to state.desktop_approved_actions.
    # 2) Graph resumes; loop re-attempts the step and executes since approval is present.
    # Interrupt data structure example:
    # {
    #   "action_id": "write_file_abcd1234",
    #   "action": "write_file",
    #   "params": {...},
    #   "reasoning": "...",
    #   "action_context": {
    #       "filename": "output.md",
    #       "will_overwrite": true,
    #       "content_preview": "..."
    #   }
    # }

    # ========================================================================
    # Tool Implementations (Basic - will be enhanced in Phase 3D)
    # ========================================================================
    def _tool_read_file(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        filename = params.get("filename") or params.get("file")
        if not filename:
            return {"success": False, "error": "No filename provided"}
        content = self.workspace_mgr.read_file(thread_id, filename)
        if content is None:
            return {"success": False, "error": f"File not found: {filename}"}
        return {"success": True, "content": content, "filename": filename, "size": len(content)}

    def _tool_write_file(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        filename = params.get("filename") or params.get("file")
        content = params.get("content", "")
        if not filename:
            return {"success": False, "error": "No filename provided"}
        filepath = self.workspace_mgr.write_file(thread_id, filename, content)
        return {"success": True, "filename": filename, "path": str(filepath), "size": len(content)}

    def _tool_edit_file(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        filename = params.get("filename") or params.get("file")
        if not filename:
            return {"success": False, "error": "No filename provided"}
        existing_content = self.workspace_mgr.read_file(thread_id, filename)
        if existing_content is None:
            return {"success": False, "error": f"File not found: {filename}"}
        new_content = params.get("content", existing_content)
        filepath = self.workspace_mgr.write_file(thread_id, filename, new_content)
        return {
            "success": True,
            "filename": filename,
            "path": str(filepath),
            "size": len(new_content),
            "changes": {"old_size": len(existing_content), "new_size": len(new_content)},
        }

    def _tool_delete_file(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        filename = params.get("filename") or params.get("file")
        if not filename:
            return {"success": False, "error": "No filename provided"}
        deleted = self.workspace_mgr.delete_file(thread_id, filename)
        if not deleted:
            return {"success": False, "error": f"File not found: {filename}"}
        return {"success": True, "filename": filename, "deleted": True}

    def _tool_list_files(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        pattern = params.get("pattern", "*")
        files = self.workspace_mgr.list_files(thread_id, pattern)
        return {"success": True, "files": [str(f.relative_to(workspace_dir)) for f in files], "count": len(files)}

    def _tool_edit_document(self, params: Dict[str, Any], workspace_dir: Path, thread_id: str) -> Dict[str, Any]:
        """Call doc-agent to apply structured DOCX operations."""
        doc_result = self.doc_edit_tool.edit_document(params, workspace_dir, thread_id)
        if not doc_result.get("success"):
            return doc_result
        return {
            "success": True,
            "doc_id": doc_result.get("doc_id"),
            "file_path": doc_result.get("file_path"),
            "change_summary": doc_result.get("change_summary"),
            "structure": doc_result.get("structure"),
            "output": doc_result.get("output"),
        }

    def _tool_generate_document(
        self,
        params: Dict[str, Any],
        workspace_dir: Path,
        thread_id: str,
        state: Optional[RAGState] = None,
    ) -> Dict[str, Any]:
        """Generate document tool using docgen subgraph wrapper."""
        result = self.docgen_tool.generate_document(
            params=params,
            workspace_dir=workspace_dir,
            thread_id=thread_id,
            state=state,
        )

        if result.get("success") and not result.get("eviction", {}).get("evicted"):
            output = result.get("output", "")
            if len(str(output)) > self.evictor.max_inline_size:
                eviction = self.evictor.process_result(
                    tool_name="generate_document",
                    result=output,
                    workspace_dir=workspace_dir,
                )
                result["eviction"] = eviction
                result["output"] = eviction.get("summary", str(output)[:500])
        return result


def node_deep_desktop_loop(state: RAGState) -> Dict[str, Any]:
    """Node wrapper for deep desktop loop."""
    loop = DeepDesktopLoop()
    return loop.run(state)
