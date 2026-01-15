"""
Tracing utilities for LangGraph subgraphs.

Provides a decorator to wrap subgraph nodes (sync or async) and append
structured execution traces with lightweight state snapshots.
"""
import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict


def _snapshot_state(state: Any) -> Dict[str, str]:
    """
    Take a lightweight snapshot of state for logging without pulling large fields.
    """
    excluded_keys = {"messages", "retrieved_docs"}
    state_view = state if isinstance(state, dict) else getattr(state, "__dict__", {}) or {}
    return {k: str(v)[:100] for k, v in state_view.items() if k not in excluded_keys}


def _merge_traces(state_view: Dict[str, Any], node_name: str, entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge existing traces from state with the new entry.
    """
    trace = list((state_view or {}).get("execution_trace", []) or [])
    trace.append(node_name)

    verbose = list((state_view or {}).get("execution_trace_verbose", []) or [])
    verbose.append(entry)

    return {"execution_trace": trace, "execution_trace_verbose": verbose}


def wrap_subgraph_node(node_name: str) -> Callable:
    """
    Decorator for subgraph nodes to record entry/exit metadata and append traces.
    """

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):

            async def _async_wrapper(state: Any):
                state_view = state if isinstance(state, dict) else getattr(state, "__dict__", {}) or {}
                start = time.perf_counter()
                entry = {
                    "node": node_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "state_snapshot": _snapshot_state(state),
                }

                result = await fn(state)

                entry.update(
                    {
                        "duration_ms": int((time.perf_counter() - start) * 1000),
                        "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                    }
                )

                merged = _merge_traces(state_view, node_name, entry)
                if isinstance(result, dict):
                    return {**result, **merged}
                return merged

            return _async_wrapper

        def _sync_wrapper(state: Any):
            state_view = state if isinstance(state, dict) else getattr(state, "__dict__", {}) or {}
            start = time.perf_counter()
            entry = {
                "node": node_name,
                "timestamp": datetime.utcnow().isoformat(),
                "state_snapshot": _snapshot_state(state),
            }

            result = fn(state)

            entry.update(
                {
                    "duration_ms": int((time.perf_counter() - start) * 1000),
                    "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                }
            )

            merged = _merge_traces(state_view, node_name, entry)
            if isinstance(result, dict):
                return {**result, **merged}
            return merged

        return _sync_wrapper

    return decorator

