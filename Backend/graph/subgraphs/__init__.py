"""
Subgraphs for the LangGraph system
"""
from .db_retrieval_subgraph import build_db_retrieval_subgraph, call_db_retrieval_subgraph
from .webcalcs_subgraph import build_webcalcs_subgraph, call_webcalcs_subgraph
from .desktop_agent_subgraph import build_desktop_agent_subgraph, call_desktop_agent_subgraph
from .build_model_gen_subgraph import build_build_model_gen_subgraph, call_build_model_gen_subgraph

__all__ = [
    "build_db_retrieval_subgraph",
    "call_db_retrieval_subgraph",
    "build_webcalcs_subgraph",
    "call_webcalcs_subgraph",
    "build_desktop_agent_subgraph",
    "call_desktop_agent_subgraph",
    "build_build_model_gen_subgraph",
    "call_build_model_gen_subgraph",
]
