"""
Wrapper for run_agentic_rag that adds LLM-based thinking logs
Intercepts execution state and generates intelligent explanations
"""
from typing import Dict, Optional, List
import time
from .execution_state import ExecutionStateCollector
from .llm_thinking_generator import LLMThinkingGenerator
from main import run_agentic_rag  # Import existing function
from langchain_core.documents import Document


class RAGWrapper:
    """Wraps RAG execution to capture state and generate thinking logs"""
    
    def __init__(self):
        self.collector = ExecutionStateCollector()
        self.thinking_generator = LLMThinkingGenerator()
    
    def run_with_thinking_logs(
        self,
        question: str,
        session_id: str = "default",
        data_sources: Optional[Dict[str, bool]] = None,
        images_base64: Optional[List[str]] = None
    ) -> Dict:
        """
        Wraps run_agentic_rag and adds thinking logs.
        This hooks into the graph execution to capture state at each node.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 RAGWrapper.run_with_thinking_logs: images_base64={images_base64 is not None}, count={len(images_base64) if images_base64 else 0}")
        
        # Reset collector
        self.collector = ExecutionStateCollector()
        self.collector.user_query = question
        
        # Call original function
        logger.info(f"🔄 Calling run_agentic_rag with images_base64={images_base64 is not None}")
        result = run_agentic_rag(
            question=question,
            session_id=session_id,
            data_sources=data_sources,
            images_base64=images_base64
        )
        
        # Extract state from result and generate thinking logs
        self._capture_state_from_result(result, question, data_sources)
        
        # Generate thinking logs using LLM
        try:
            thinking_logs = self.thinking_generator.generate_thinking_logs(self.collector)
        except Exception as e:
            # Fallback if LLM generation fails
            thinking_logs = [
                f"## 🎯 Query Processing\n\nProcessing your query: '{question}'",
                f"## ✅ Processing Complete\n\nQuery processed successfully"
            ]
        
        # Add thinking logs to result
        result["thinking_log"] = thinking_logs
        
        return result
    
    def _capture_state_from_result(self, result: Dict, query: str, data_sources: Dict):
        """Extract execution state from result dict"""
        # Capture planning
        if result.get("query_plan"):
            plan = result["query_plan"]
            self.collector.capture_planning(
                query=query,
                plan=plan,
                reasoning=plan.get("reasoning", "")
            )
        
        # Capture retrieval - need to convert dicts to Document objects if needed
        retrieved_docs = result.get("retrieved_docs", [])
        code_docs = result.get("retrieved_code_docs", [])
        coop_docs = result.get("retrieved_coop_docs", [])
        
        # Convert dicts to Document objects if needed
        if retrieved_docs and isinstance(retrieved_docs[0], dict):
            retrieved_docs = [Document(**doc) if isinstance(doc, dict) else doc for doc in retrieved_docs]
        if code_docs and isinstance(code_docs[0], dict):
            code_docs = [Document(**doc) if isinstance(doc, dict) else doc for doc in code_docs]
        if coop_docs and isinstance(coop_docs[0], dict):
            coop_docs = [Document(**doc) if isinstance(doc, dict) else doc for doc in coop_docs]
        
        if retrieved_docs or code_docs or coop_docs:
            self.collector.capture_retrieval(
                query=query,
                retrieved_docs=retrieved_docs,
                code_docs=code_docs,
                coop_docs=coop_docs,
                route=result.get("data_route"),
                data_sources=data_sources
            )
        
        # Capture grading
        graded_docs = result.get("graded_docs", [])
        graded_code = result.get("graded_code_docs", [])
        graded_coop = result.get("graded_coop_docs", [])
        
        # Convert dicts to Document objects if needed
        if graded_docs and isinstance(graded_docs[0], dict):
            graded_docs = [Document(**doc) if isinstance(doc, dict) else doc for doc in graded_docs]
        
        if graded_docs or graded_code or graded_coop:
            total_retrieved = len(retrieved_docs) + len(code_docs) + len(coop_docs)
            self.collector.capture_grading(
                query=query,
                retrieved_count=total_retrieved,
                graded_count=len(graded_docs),
                code_graded=len(graded_code),
                coop_graded=len(graded_coop)
            )
        
        # Capture synthesis
        answer = result.get("answer") or result.get("final_answer")
        citations = result.get("citations") or result.get("answer_citations", [])
        code_answer = result.get("code_answer")
        coop_answer = result.get("coop_answer")
        
        # Convert graded_docs to Document objects if needed
        if graded_docs and isinstance(graded_docs[0], dict):
            graded_docs = [Document(**doc) if isinstance(doc, dict) else doc for doc in graded_docs]
        
        if answer:
            self.collector.capture_synthesis(
                query=query,
                graded_docs=graded_docs,
                answer=answer,
                citations=citations,
                code_answer=code_answer,
                coop_answer=coop_answer
            )


# Global wrapper instance
_wrapper = RAGWrapper()

def run_agentic_rag_with_thinking_logs(
    question: str,
    session_id: str = "default",
    data_sources: Optional[Dict[str, bool]] = None,
    images_base64: Optional[List[str]] = None
) -> Dict:
    """Public function to call RAG with thinking logs"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 run_agentic_rag_with_thinking_logs called with images_base64={images_base64 is not None}, count={len(images_base64) if images_base64 else 0}")
    return _wrapper.run_with_thinking_logs(
        question=question,
        session_id=session_id,
        data_sources=data_sources,
        images_base64=images_base64
    )

