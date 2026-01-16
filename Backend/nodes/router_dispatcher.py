"""
Router Dispatcher Node
Dispatches to the appropriate router nodes based on selected_routers
Runs selected routers in parallel
"""
import time
from concurrent.futures import ThreadPoolExecutor
from langgraph.errors import GraphInterrupt
from models.parent_state import ParentState
from graph.subgraphs.db_retrieval_subgraph import call_db_retrieval_subgraph
from graph.subgraphs.webcalcs_subgraph import call_webcalcs_subgraph
from graph.subgraphs.desktop_agent_subgraph import call_desktop_agent_subgraph
from config.logging_config import log_route


def _requires_desktop_agent(state: ParentState) -> bool:
    """Determine whether the desktop agent should be invoked."""
    if getattr(state, "requires_desktop_action", False):
        return True

    workflow = getattr(state, "workflow", None)
    task_type = getattr(state, "task_type", None)
    if workflow == "docgen" or task_type in {"doc_section", "doc_report"}:
        return True

    selected_app = getattr(state, "selected_app", "") or ""
    desktop_tools = getattr(state, "desktop_tools", []) or []
    if selected_app or desktop_tools:
        return True

    # Keyword heuristic on latest user message
    user_query = getattr(state, "user_query", "") or ""
    latest_message = ""
    if getattr(state, "messages", None):
        try:
            latest_message = (state.messages[-1] or {}).get("content", "")
        except Exception:
            latest_message = ""
    text = f"{user_query} {latest_message}".lower()
    desktop_keywords = ["excel", "spreadsheet", "word", ".docx", "desktop", "revit", "cad", "file path"]
    return any(k in text for k in desktop_keywords)


def node_router_dispatcher(state: ParentState) -> dict:
    """Dispatch to appropriate router nodes in parallel"""
    t_start = time.time()
    log_route.info(">>> ROUTER DISPATCHER START")

    selected_routers = list(getattr(state, "selected_routers", []) or [])
    if _requires_desktop_agent(state) and "desktop" not in selected_routers:
        selected_routers.append("desktop")
        try:
            state.selected_routers = selected_routers
        except Exception:
            # State may be an immutable dataclass; ignore if assignment fails
            pass

    log_route.info(f"📋 Selected routers: {selected_routers}")
    
    results = {}
    
    # CRITICAL: RAG subgraph must be called directly (not in ThreadPoolExecutor)
    # to allow GraphInterrupt exceptions to propagate correctly to the parent graph
    if "rag" in selected_routers:
        log_route.info("🚀 Dispatching to DBRetrieval subgraph")
        try:
            rag_result = call_db_retrieval_subgraph(state)
            results["rag"] = rag_result
            log_route.info("✅ RAG router completed")
        except GraphInterrupt:
            # CRITICAL: Re-raise GraphInterrupt to propagate to parent graph
            # This allows the interrupt to be handled at the API level
            raise
        except Exception as e:
            log_route.error(f"❌ RAG router failed: {e}")
            results["rag"] = {}
    
    # Other routers can run in parallel (they don't use interrupts)
    other_routers = [r for r in selected_routers if r != "rag"]
    if other_routers:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            if "web" in other_routers:
                log_route.info("🚀 Dispatching to WebCalcs subgraph")
                futures["web"] = executor.submit(call_webcalcs_subgraph, state)
            
            if "desktop" in other_routers:
                log_route.info("🚀 Dispatching to DesktopAgent subgraph")
                futures["desktop"] = executor.submit(call_desktop_agent_subgraph, state)
            
            # Collect results from other routers
            for router_name, future in futures.items():
                try:
                    result = future.result()
                    results[router_name] = result
                    log_route.info(f"✅ {router_name.upper()} router completed")
                except Exception as e:
                    log_route.error(f"❌ {router_name.upper()} router failed: {e}")
                    results[router_name] = {}
    
    # Merge results into state updates
    state_updates = {}
    
    if "rag" in results:
        rag_result = results["rag"]
        state_updates.update(rag_result)
    
    if "web" in results:
        web_result = results["web"]
        state_updates.update(web_result)
    
    if "desktop" in results:
        desktop_result = results["desktop"]
        state_updates.update(desktop_result)
    
    t_elapsed = time.time() - t_start
    log_route.info(f"<<< ROUTER DISPATCHER DONE in {t_elapsed:.2f}s")
    
    return state_updates
