"""
Search Orchestrator - uses LangGraph for execution, built directly from MD execution graphs.
MD files define the structure, LangGraph executes it.

Architecture:
- TeamOrchestrator: Fast routing (no LangGraph)
- SearchOrchestrator: Uses LangGraph for execution (this file)
- MD files: Define graph structure (retrieve_db_info.graph.md)
- LangGraph: Executes the graph (built directly from MD)
"""

import os
import json
import sys
from typing import Dict, List, Optional, Callable, Any, TypedDict
from pathlib import Path
from .base_agent import BaseAgent, AgentState
from cognition.planner import Planner

# Import execution trace
sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.trace import ExecutionTrace, ExecutionStep, StepStatus, ExecutionStatus, create_step

# LangGraph imports (will fail gracefully if not installed)
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    StateGraph = None
    END = None

# Try to import RAG system (for document searches)
try:
    # Add backend path for RAG import
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
    from RAG.rag import run_agentic_rag
    HAS_RAG = True
except ImportError:
    HAS_RAG = False
    run_agentic_rag = None


class ExecutionState(TypedDict):
    """State object for LangGraph execution."""
    user_query: str
    available_outputs: Dict[str, Any]  # Data flow tracking
    current_step: str
    results: Dict[str, Any]
    errors: List[str]
    trace: List[Dict[str, Any]]  # Execution trace


class SearchOrchestrator(BaseAgent):
    """
    Search Orchestrator using LangGraph for execution.
    
    LangGraph is built ONCE based on the MD file structure:
    - extract_search_criteria → IF incomplete → request_clarification (END)
    - extract_search_criteria → IF complete → search_projects_by_dimensions → rank_projects_by_similarity → retrieve_project_metadata
    """
    
    # Class-level workflow - built once, reused for all instances
    _langgraph_workflow = None
    _workflow_tools = None
    
    def __init__(self, api_key: Optional[str] = None, tools: List[Callable] = None):
        super().__init__(name="search_orchestrator", tools=tools)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Use core Planner for planning
        self.planner = Planner(api_key=self.api_key)
        
        # Build LangGraph ONCE if not already built
        tool_registry = {tool.__name__: tool for tool in (tools or [])}
        if SearchOrchestrator._langgraph_workflow is None and HAS_LANGGRAPH:
            SearchOrchestrator._langgraph_workflow = self._build_search_langgraph(tool_registry)
            SearchOrchestrator._workflow_tools = tool_registry
        
        self.langgraph_workflow = SearchOrchestrator._langgraph_workflow
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
            except Exception:
                self.enabled = False
        else:
            self.enabled = False
    
    def _build_search_langgraph(self, tools: Dict[str, Callable]) -> Any:
        """
        Build LangGraph workflow ONCE based on MD file structure.
        
        MD structure (retrieve_db_info.graph.md):
        1. extract_search_criteria (input: user_query, produces: dimension_constraints)
           IF incomplete → request_clarification (terminal)
           ELSE → search_projects_by_dimensions
        2. search_projects_by_dimensions (input: dimension_constraints, produces: candidate_project_ids, match_scores)
        3. rank_projects_by_similarity (input: candidate_project_ids, match_scores, produces: ranked_project_ids)
        4. retrieve_project_metadata (input: ranked_project_ids, produces: project_summaries)
        """
        if not HAS_LANGGRAPH:
            return None
        
        workflow = StateGraph(ExecutionState)
        
        # Node 1: extract_search_criteria
        def extract_node(state: ExecutionState) -> ExecutionState:
            tool_func = tools.get("extract_search_criteria")
            if tool_func:
                try:
                    state["trace"].append({
                        "step": "extract_search_criteria",
                        "thinking": f"Extracting search criteria from user query: '{state['user_query']}'",
                        "inputs": {"user_query": state["user_query"]},
                        "status": "running"
                    })
                    result = tool_func(user_query=state["user_query"])
                    if isinstance(result, dict):
                        state["available_outputs"].update(result)
                    # Check completeness for branch decision
                    dim_constraints = result.get("dimension_constraints", {})
                    is_complete = dim_constraints.get("complete", False) if isinstance(dim_constraints, dict) else False
                    thinking = f"Extracted criteria: {result}. Completeness: {is_complete}"
                    if not is_complete:
                        thinking += " → Will branch to request_clarification"
                    else:
                        thinking += " → Will continue to search_projects_by_dimensions"
                    
                    state["trace"][-1].update({
                        "outputs": result,
                        "status": "completed",
                        "thinking": thinking
                    })
                except Exception as e:
                    state["errors"].append(f"extract_search_criteria: {str(e)}")
                    state["trace"].append({
                        "step": "extract_search_criteria",
                        "inputs": {"user_query": state["user_query"]},
                        "error": str(e),
                        "status": "error",
                        "thinking": f"Error extracting criteria: {str(e)}"
                    })
            return state
        
        # Node 2: request_clarification (terminal)
        def clarify_node(state: ExecutionState) -> ExecutionState:
            tool_func = tools.get("request_clarification")
            if tool_func:
                try:
                    dim_constraints = state["available_outputs"].get("dimension_constraints", {})
                    missing_fields = []
                    if not dim_constraints.get("dimensions"):
                        missing_fields.append("dimensions")
                    if not dim_constraints.get("building_type"):
                        missing_fields.append("building type")
                    if not dim_constraints.get("material"):
                        missing_fields.append("material")
                    
                    thinking = f"Requesting clarification for missing fields: {missing_fields}. This is a terminal step - workflow ends here."
                    state["trace"].append({
                        "step": "request_clarification",
                        "thinking": thinking,
                        "inputs": {"missing_fields": missing_fields},
                        "status": "running"
                    })
                    
                    result = tool_func(missing_fields=missing_fields)
                    if isinstance(result, dict):
                        state["available_outputs"].update(result)
                    
                    state["trace"][-1].update({
                        "outputs": result,
                        "status": "completed"
                    })
                except Exception as e:
                    state["errors"].append(f"request_clarification: {str(e)}")
                    state["trace"].append({
                        "step": "request_clarification",
                        "thinking": f"Error requesting clarification: {str(e)}",
                        "error": str(e),
                        "status": "error"
                    })
            return state
        
        # Node 3: search_projects_by_dimensions
        def search_node(state: ExecutionState) -> ExecutionState:
            tool_func = tools.get("search_projects_by_dimensions")
            if tool_func:
                try:
                    dim_constraints = state["available_outputs"].get("dimension_constraints", {})
                    thinking = f"Searching Supabase via GraphQL for projects matching: {dim_constraints}"
                    state["trace"].append({
                        "step": "search_projects_by_dimensions",
                        "thinking": thinking,
                        "inputs": {"dimension_constraints": dim_constraints},
                        "status": "running"
                    })
                    
                    result = tool_func(dimension_constraints=dim_constraints)
                    # Tool returns list of dicts, need to extract IDs and scores
                    if isinstance(result, list):
                        candidate_ids = [p.get("project_id") for p in result]
                        match_scores = [p.get("match_score", 0) for p in result]
                        state["available_outputs"]["candidate_project_ids"] = candidate_ids
                        state["available_outputs"]["match_scores"] = match_scores
                        thinking += f" → Found {len(candidate_ids)} candidate projects"
                    
                    state["trace"][-1].update({
                        "outputs": {"candidate_project_ids": state["available_outputs"].get("candidate_project_ids"), "match_scores": state["available_outputs"].get("match_scores")},
                        "status": "completed",
                        "thinking": thinking
                    })
                except Exception as e:
                    state["errors"].append(f"search_projects_by_dimensions: {str(e)}")
                    state["trace"].append({
                        "step": "search_projects_by_dimensions",
                        "thinking": f"Error searching projects: {str(e)}",
                        "error": str(e),
                        "status": "error"
                    })
            return state
        
        # Node 4: rank_projects_by_similarity
        def rank_node(state: ExecutionState) -> ExecutionState:
            tool_func = tools.get("rank_projects_by_similarity")
            if tool_func:
                try:
                    candidate_ids = state["available_outputs"].get("candidate_project_ids", [])
                    match_scores = state["available_outputs"].get("match_scores", [])
                    thinking = f"Ranking {len(candidate_ids)} candidate projects by similarity scores"
                    state["trace"].append({
                        "step": "rank_projects_by_similarity",
                        "thinking": thinking,
                        "inputs": {"candidate_project_ids": candidate_ids, "match_scores": match_scores},
                        "status": "running"
                    })
                    
                    # Build candidate_projects list for tool
                    candidate_projects = [
                        {"project_id": pid, "match_score": score}
                        for pid, score in zip(candidate_ids, match_scores)
                    ]
                    result = tool_func(candidate_projects=candidate_projects)
                    # Tool returns list of ranked IDs
                    if isinstance(result, list):
                        state["available_outputs"]["ranked_project_ids"] = result
                        thinking += f" → Ranked top {len(result)} projects"
                    
                    state["trace"][-1].update({
                        "outputs": {"ranked_project_ids": result},
                        "status": "completed",
                        "thinking": thinking
                    })
                except Exception as e:
                    state["errors"].append(f"rank_projects_by_similarity: {str(e)}")
                    state["trace"].append({
                        "step": "rank_projects_by_similarity",
                        "thinking": f"Error ranking projects: {str(e)}",
                        "error": str(e),
                        "status": "error"
                    })
            return state
        
        # Node 5: retrieve_project_metadata
        def retrieve_node(state: ExecutionState) -> ExecutionState:
            tool_func = tools.get("retrieve_project_metadata")
            if tool_func:
                try:
                    ranked_ids = state["available_outputs"].get("ranked_project_ids", [])
                    thinking = f"Retrieving metadata from Supabase via GraphQL for {len(ranked_ids)} ranked projects"
                    state["trace"].append({
                        "step": "retrieve_project_metadata",
                        "thinking": thinking,
                        "inputs": {"ranked_project_ids": ranked_ids},
                        "status": "running"
                    })
                    
                    result = tool_func(project_ids=ranked_ids)
                    # Tool returns list of project summaries
                    if isinstance(result, list):
                        state["available_outputs"]["project_summaries"] = result
                        state["results"] = {"project_summaries": result}
                        thinking += f" → Retrieved {len(result)} project summaries"
                    
                    state["trace"][-1].update({
                        "outputs": {"project_summaries": result},
                        "status": "completed",
                        "thinking": thinking
                    })
                except Exception as e:
                    state["errors"].append(f"retrieve_project_metadata: {str(e)}")
                    state["trace"].append({
                        "step": "retrieve_project_metadata",
                        "thinking": f"Error retrieving metadata: {str(e)}",
                        "error": str(e),
                        "status": "error"
                    })
            return state
        
        # Branch function: check if dimension_constraints are incomplete
        def check_incomplete(state: ExecutionState) -> str:
            dim_constraints = state["available_outputs"].get("dimension_constraints", {})
            is_complete = True
            if isinstance(dim_constraints, dict):
                is_complete = dim_constraints.get("complete", True)
            
            # Log branch decision
            if not is_complete:
                state["trace"].append({
                    "step": "branch_decision",
                    "thinking": f"🔀 Branch Decision: dimension_constraints incomplete → routing to request_clarification",
                    "inputs": {"dimension_constraints": dim_constraints},
                    "outputs": {"decision": "branch", "target": "request_clarification"},
                    "status": "completed"
                })
                return "branch"  # Go to request_clarification
            else:
                state["trace"].append({
                    "step": "branch_decision",
                    "thinking": f"🔀 Branch Decision: dimension_constraints complete → continuing to search_projects_by_dimensions",
                    "inputs": {"dimension_constraints": dim_constraints},
                    "outputs": {"decision": "continue", "target": "search_projects_by_dimensions"},
                    "status": "completed"
                })
                return "continue"  # Continue to search
        
        # Add nodes
        workflow.add_node("extract", extract_node)
        workflow.add_node("clarify", clarify_node)
        workflow.add_node("search", search_node)
        workflow.add_node("rank", rank_node)
        workflow.add_node("retrieve", retrieve_node)
        
        # Set entry point
        workflow.set_entry_point("extract")
        
        # Conditional edge: extract → IF incomplete → clarify (END), ELSE → search
        workflow.add_conditional_edges(
            "extract",
            check_incomplete,
            {
                "branch": "clarify",  # IF incomplete
                "continue": "search"  # IF complete
            }
        )
        
        # Terminal edge: clarify → END
        workflow.add_edge("clarify", END)
        
        # Sequential edges: search → rank → retrieve → END
        workflow.add_edge("search", "rank")
        workflow.add_edge("rank", "retrieve")
        workflow.add_edge("retrieve", END)
        
        # Compile and return
        return workflow.compile()
    
    
    def plan_search(self, user_query: str) -> Dict:
        """Generate plan using core Planner."""
        return self.planner.generate_plan(
            user_query=user_query,
            available_tools=self.tools,
            domain="search",
            context={
                "data_sources": ["Supabase", "GraphQL"],
                "execution_mode": "cloud-only"
            }
        )
    
    def execute(self, task: str, context: Dict = None) -> Dict:
        """
        Execute search using LangGraph workflow built from MD graph.
        
        Args:
            task: Search query from user
            context: Additional context
            
        Returns:
            Dict with execution results
        """
        context = context or {}
        
        # Initialize state
        self.state = AgentState(
            task=task,
            context=context,
            completed_steps=[],
            results={}
        )
        
        # Create execution trace
        trace = ExecutionTrace()
        trace.available_outputs = {"user_query": task}
        
        # Add strategic planning info from TeamOrchestrator
        strategic_planning = context.get("planning", {})
        needs_rag = False
        rag_result = None
        
        if strategic_planning:
            intent = strategic_planning.get("intent", "unknown")
            data_sources = strategic_planning.get("data_sources", [])
            strategy = strategic_planning.get("strategy", "unknown")
            reasoning = strategic_planning.get("reasoning", "")
            
            trace.thinking_log.append(f"🎯 Strategic Planning:")
            trace.thinking_log.append(f"   Intent: {intent}")
            trace.thinking_log.append(f"   Data Sources: {', '.join(data_sources)}")
            trace.thinking_log.append(f"   Strategy: {strategy}")
            if reasoning:
                trace.thinking_log.append(f"   Reasoning: {reasoning}")
            
            # Check if we need RAG (document search) based on strategic planning
            if any("rag" in source.lower() or "document" in source.lower() for source in data_sources):
                needs_rag = True
        
        # Execute RAG if needed (before LangGraph workflow)
        if needs_rag and HAS_RAG and run_agentic_rag:
            try:
                session_id = context.get("session_id", "default")
                data_sources_config = context.get("data_sources", {})
                
                trace.thinking_log.append(f"📚 Starting RAG search for document retrieval...")
                rag_result = run_agentic_rag(
                    question=task,
                    session_id=session_id,
                    data_sources=data_sources_config
                )
                
                # Add RAG results to thinking log
                trace.thinking_log.append(f"📚 RAG Search Completed:")
                if rag_result.get("answer"):
                    answer_preview = rag_result['answer'][:200] + "..." if len(rag_result['answer']) > 200 else rag_result['answer']
                    trace.thinking_log.append(f"   Answer Preview: {answer_preview}")
                if rag_result.get("citations"):
                    trace.thinking_log.append(f"   Citations: {len(rag_result['citations'])} documents")
            except Exception as e:
                trace.thinking_log.append(f"⚠️ RAG search failed: {str(e)}")
                rag_result = None
        
        # Generate plan using core Planner
        plan = self.plan_search(task)
        
        # Get thinking explanation
        if self.planner.enabled and plan.get("plan"):
            thinking = self.planner.explain_thinking(task, plan)
            plan["thinking"] = thinking
        
        trace.thinking_log.append(f"🔍 Planning search for: {task}")
        trace.thinking_log.append(f"📋 Using LangGraph workflow built from retrieve_db_info.graph.md")
        if plan.get("reasoning"):
            trace.thinking_log.append(f"💭 Planning reasoning: {plan['reasoning']}")
        if plan.get("thinking"):
            trace.thinking_log.append(f"🧠 Planner thinking: {plan['thinking']}")
        
        result = {
            "plan": plan,
            "steps": [],
            "trace": trace,
            "results": None,
            "success": False
        }
        
        # Execute using LangGraph if available
        if self.langgraph_workflow:
            try:
                # Initialize LangGraph state
                langgraph_state: ExecutionState = {
                    "user_query": task,
                    "available_outputs": {"user_query": task},
                    "current_step": "",
                    "results": {},
                    "errors": [],
                    "trace": []
                }
                
                # Execute LangGraph workflow
                final_state = self.langgraph_workflow.invoke(langgraph_state)
                
                # Convert LangGraph trace to ExecutionTrace
                step_number = 1
                for step_trace in final_state.get("trace", []):
                    # Skip branch_decision steps (they're logged but not counted as execution steps)
                    if step_trace.get("step") == "branch_decision":
                        trace.thinking_log.append(step_trace.get("thinking", "Branch decision made"))
                        continue
                    
                    step = create_step(
                        step_number=step_number,
                        tool_name=step_trace.get("step", "unknown"),
                        location="cloud",
                        inputs=step_trace.get("inputs", {}),
                        outputs=step_trace.get("outputs", {}),
                        status=StepStatus.COMPLETED if "error" not in step_trace and step_trace.get("status") != "error" else StepStatus.ERROR,
                        error=step_trace.get("error"),
                        thinking=step_trace.get("thinking", f"Executing {step_trace.get('step')} from MD graph workflow")
                    )
                    trace.steps.append(step)
                    step_number += 1
                
                # Update trace with final state
                trace.available_outputs = final_state.get("available_outputs", {})
                
                if final_state.get("errors"):
                    trace.errors.extend(final_state["errors"])
                    trace.final_status = ExecutionStatus.BLOCKED
                else:
                    trace.final_status = ExecutionStatus.READY
                
                # Get final results
                final_results = final_state.get("results") or {}
                
                # Combine with RAG results if available
                if rag_result:
                    if isinstance(final_results, dict):
                        final_results["rag_answer"] = rag_result.get("answer", "")
                        final_results["rag_citations"] = rag_result.get("citations", [])
                    elif isinstance(final_results, str):
                        # Convert to dict to add RAG results
                        final_results = {
                            "metadata_results": final_results,
                            "rag_answer": rag_result.get("answer", ""),
                            "rag_citations": rag_result.get("citations", [])
                        }
                    else:
                        final_results = {
                            "metadata_results": final_results,
                            "rag_answer": rag_result.get("answer", ""),
                            "rag_citations": rag_result.get("citations", [])
                        }
                
                result["results"] = final_results
                result["success"] = True
                
                # Convert to backward-compatible format
                for step_trace in final_state.get("trace", []):
                    result["steps"].append({
                        "tool": step_trace.get("step"),
                        "args": step_trace.get("inputs", {}),
                        "result": step_trace.get("outputs", {}),
                        "status": step_trace.get("status", "completed")
                    })
                
            except Exception as e:
                trace.errors.append(f"LangGraph execution failed: {str(e)}")
                trace.final_status = ExecutionStatus.BLOCKED
                result["error"] = str(e)
        else:
            # Fallback: manual execution if LangGraph not available
            trace.errors.append("LangGraph not available - install langgraph package")
            trace.final_status = ExecutionStatus.BLOCKED
            result["error"] = "LangGraph not available"
        
        result["trace"] = trace
        return result

