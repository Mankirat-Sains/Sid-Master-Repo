"""
Router Dispatcher Node
Dispatches to the appropriate router nodes based on selected_routers
Runs selected routers in parallel
"""
import time
from concurrent.futures import ThreadPoolExecutor
from models.rag_state import RAGState
from nodes.route import node_route
from nodes.web_router import node_web_router
from nodes.desktop_router import node_desktop_router
from config.logging_config import log_route


def node_router_dispatcher(state: RAGState) -> dict:
    """Dispatch to appropriate router nodes in parallel"""
    t_start = time.time()
    log_route.info(">>> ROUTER DISPATCHER START")
    
    selected_routers = state.selected_routers or []
    log_route.info(f"📋 Selected routers: {selected_routers}")
    
    results = {}
    
    # Run selected routers in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        
        if "rag" in selected_routers:
            log_route.info("🚀 Dispatching to RAG router")
            futures["rag"] = executor.submit(node_route, state)
        
        if "web" in selected_routers:
            log_route.info("🚀 Dispatching to Web router")
            futures["web"] = executor.submit(node_web_router, state)
        
        if "desktop" in selected_routers:
            log_route.info("🚀 Dispatching to Desktop router")
            futures["desktop"] = executor.submit(node_desktop_router, state)
        
        # Collect results
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

