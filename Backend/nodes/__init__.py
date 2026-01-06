"""LangGraph Nodes for RAG System"""
# Top-level orchestration nodes
from .plan import node_plan
from .router_dispatcher import node_router_dispatcher

# RAG node - wrapper that runs rag_plan and rag_router in parallel
from .DBRetrieval.rag import node_rag

# RAG sub-nodes (run in parallel internally by node_rag)
from .DBRetrieval.rag_plan import node_rag_plan
from .DBRetrieval.rag_router import node_rag_router

# DBRetrieval pipeline nodes
from .DBRetrieval.retrieve import node_retrieve
from .DBRetrieval.grade import node_grade
from .DBRetrieval.answer import node_answer
from .DBRetrieval.verify import node_verify, _verify_route
from .DBRetrieval.correct import node_correct
from .DBRetrieval.image_nodes import node_generate_image_embeddings, node_image_similarity_search

# Router nodes
from .WebCalcs.web_router import node_web_router
from .DesktopAgent.desktop_router import node_desktop_router

