"""
Subgraphs for the LangGraph system.
"""
from .db_retrieval_subgraph import build_db_retrieval_subgraph, call_db_retrieval_subgraph
from .desktop_agent_subgraph import build_desktop_agent_subgraph, call_desktop_agent_subgraph
from .document_generation_subgraph import build_doc_generation_subgraph, call_doc_generation_subgraph

__all__ = [
    "build_db_retrieval_subgraph",
    "call_db_retrieval_subgraph",
    "build_desktop_agent_subgraph",
    "call_desktop_agent_subgraph",
    "build_doc_generation_subgraph",
    "call_doc_generation_subgraph",
]
