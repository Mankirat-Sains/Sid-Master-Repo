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


def node_router_dispatcher(state: ParentState) -> dict:
    """Dispatch to appropriate router nodes in parallel"""
    t_start = time.time()
    log_route.info(">>> ROUTER DISPATCHER START")
    
    selected_routers = state.selected_routers or []
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

