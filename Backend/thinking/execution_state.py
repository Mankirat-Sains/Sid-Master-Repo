"""
Captures execution state at each node for thinking log generation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from langchain_core.documents import Document

@dataclass
class NodeExecutionState:
    """State captured at a specific node execution"""
    node_name: str
    user_query: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

@dataclass
class ExecutionStateCollector:
    """Collects execution state throughout the RAG pipeline"""
    states: List[NodeExecutionState] = field(default_factory=list)
    user_query: str = ""
    
    def capture_planning(self, query: str, plan: Dict, reasoning: str):
        """Capture planning state"""
        self.user_query = query
        self.states.append(NodeExecutionState(
            node_name="plan",
            user_query=query,
            inputs={"query": query},
            outputs={
                "plan": plan,
                "reasoning": reasoning,
                "steps": plan.get("steps", []),
                "subqueries": plan.get("subqueries", [])
            }
        ))
    
    def capture_retrieval(self, query: str, retrieved_docs: List[Document], 
                         code_docs: List[Document] = None, coop_docs: List[Document] = None,
                         route: str = None, data_sources: Dict = None):
        """Capture retrieval state"""
        # Extract project info from docs
        projects = set()
        for doc in retrieved_docs:
            proj = (doc.metadata or {}).get("drawing_number") or (doc.metadata or {}).get("project_key")
            if proj:
                projects.add(proj)
        
        # Extract sample content
        sample_chunks = []
        for doc in retrieved_docs[:3]:
            content = doc.page_content[:300] if doc.page_content else ""
            sample_chunks.append({
                "content": content,
                "project": (doc.metadata or {}).get("drawing_number") or (doc.metadata or {}).get("project_key", "Unknown"),
                "page": (doc.metadata or {}).get("page_id", "Unknown")
            })
        
        self.states.append(NodeExecutionState(
            node_name="retrieve",
            user_query=query,
            inputs={"query": query, "route": route, "data_sources": data_sources},
            outputs={
                "retrieved_count": len(retrieved_docs),
                "code_count": len(code_docs) if code_docs else 0,
                "coop_count": len(coop_docs) if coop_docs else 0,
                "projects": list(projects),
                "sample_chunks": sample_chunks
            }
        ))
    
    def capture_grading(self, query: str, retrieved_count: int, graded_count: int,
                       code_graded: int = 0, coop_graded: int = 0):
        """Capture grading state"""
        self.states.append(NodeExecutionState(
            node_name="grade",
            user_query=query,
            inputs={"retrieved_count": retrieved_count},
            outputs={
                "graded_count": graded_count,
                "code_graded": code_graded,
                "coop_graded": coop_graded,
                "filtered_out": retrieved_count - graded_count
            }
        ))
    
    def capture_synthesis(self, query: str, graded_docs: List[Document],
                         answer: str, citations: List, code_answer: str = None, coop_answer: str = None):
        """Capture synthesis state"""
        self.states.append(NodeExecutionState(
            node_name="answer",
            user_query=query,
            inputs={"graded_docs_count": len(graded_docs)},
            outputs={
                "answer_length": len(answer) if answer else 0,
                "citations_count": len(citations) if citations else 0,
                "has_code_answer": bool(code_answer),
                "has_coop_answer": bool(coop_answer)
            }
        ))



