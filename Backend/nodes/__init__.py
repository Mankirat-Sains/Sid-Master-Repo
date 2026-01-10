"""LangGraph Nodes for RAG System"""
# Top-level orchestration nodes
from .plan import node_plan
from .router_dispatcher import node_router_dispatcher

# RAG node - wrapper that runs rag_plan and rag_router in parallel
from .DBRetrieval.SQLdb.rag import node_rag

# RAG sub-nodes (run in parallel internally by node_rag)
from .DBRetrieval.SQLdb.rag_plan import node_rag_plan
from .DBRetrieval.SQLdb.rag_router import node_rag_router

# DBRetrieval pipeline nodes
from .DBRetrieval.SQLdb.retrieve import node_retrieve
from .DBRetrieval.SQLdb.grade import node_grade
from .DBRetrieval.SQLdb.answer import node_answer
from .DBRetrieval.SQLdb.verify import node_verify, _verify_route
from .DBRetrieval.SQLdb.correct import node_correct
from .DBRetrieval.SQLdb.image_nodes import node_generate_image_embeddings, node_image_similarity_search

# Router nodes
from .WebCalcs.web_router import node_web_router
from .DesktopAgent.desktop_router import node_desktop_router

