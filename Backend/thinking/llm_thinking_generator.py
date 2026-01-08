"""
LLM-based thinking log generator
Uses LLM to generate intelligent, adaptable explanations of execution
"""
from typing import List, Dict, Any
from config.llm_instances import llm_fast
from langchain_core.prompts import ChatPromptTemplate
from .execution_state import ExecutionStateCollector, NodeExecutionState

class LLMThinkingGenerator:
    """Generates human-readable thinking logs using LLM"""
    
    def __init__(self):
        self.llm = llm_fast
    
    def generate_thinking_logs(self, collector: ExecutionStateCollector) -> List[str]:
        """Generate thinking logs from execution state"""
        thinking_logs = []
        
        # Add initial thinking log
        thinking_logs.append(f"## 🎯 Starting Query Processing\n\n**Your query:** '{collector.user_query}'\n\nI'm analyzing your question and determining the best approach to find the answer.")
        
        for state in collector.states:
            if state.node_name == "plan":
                thinking_logs.append(self._explain_planning(state))
            elif state.node_name == "retrieve":
                thinking_logs.append(self._explain_retrieval(state))
            elif state.node_name == "grade":
                thinking_logs.append(self._explain_grading(state))
            elif state.node_name == "answer":
                thinking_logs.append(self._explain_synthesis(state))
        
        return thinking_logs
    
    def _explain_planning(self, state: NodeExecutionState) -> str:
        """Use LLM to explain planning process"""
        plan = state.outputs.get("plan", {})
        reasoning = state.outputs.get("reasoning", "")
        steps = state.outputs.get("steps", [])
        subqueries = state.outputs.get("subqueries", [])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining the query planning process to a user.
Your job is to explain in clear, conversational language:
1. What the user asked
2. How the query was broken down
3. What operations will be performed
4. Why this approach was chosen

Be specific about the steps and explain the reasoning. Use markdown formatting with ## for main sections and ** for emphasis."""),
            ("user", """User Query: "{query}"

Planning Reasoning: {reasoning}

Query Plan Steps:
{steps}

Subqueries Generated:
{subqueries}

Generate a clear explanation of the planning process. Start with "## 📋 Planning Query" and explain what will happen. Be conversational and helpful."""),
        ])
        
        steps_str = "\n".join([
            f"{i+1}. **{s.get('op', '?')}** - {s.get('args', {})}"
            for i, s in enumerate(steps)
        ])
        subqueries_str = "\n".join([f"- {q}" for q in subqueries[:5]])
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=state.user_query,
                reasoning=reasoning,
                steps=steps_str,
                subqueries=subqueries_str
            ))
            return response.content
        except Exception as e:
            # Fallback if LLM fails
            return f"## 📋 Planning Query\n\n**Reasoning:** {reasoning}\n\n**Steps:** {len(steps)} operations planned\n\n**Subqueries:** {len(subqueries)} queries generated"
    
    def _explain_retrieval(self, state: NodeExecutionState) -> str:
        """Use LLM to explain retrieval process"""
        retrieved_count = state.outputs.get("retrieved_count", 0)
        code_count = state.outputs.get("code_count", 0)
        coop_count = state.outputs.get("coop_count", 0)
        projects = state.outputs.get("projects", [])
        sample_chunks = state.outputs.get("sample_chunks", [])
        route = state.inputs.get("route", "smart")
        data_sources = state.inputs.get("data_sources", {})
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining the document retrieval process.
Explain:
1. What databases were searched
2. How many documents were found
3. Which projects they came from
4. Why these documents are relevant
5. What the search strategy was

Be specific about numbers and projects. Use markdown formatting. Be conversational and explain the process clearly."""),
            ("user", """User Query: "{query}"

Search Configuration:
- Route: {route}
- Project DB: {project_db}
- Code DB: {code_db}
- Coop DB: {coop_db}

Results:
- Project documents retrieved: {retrieved_count}
- Code documents retrieved: {code_count}
- Coop documents retrieved: {coop_count}
- Projects found: {projects}

Sample Document Chunks:
{samples}

Explain the retrieval process and why these documents were selected. Start with "## 📚 Retrieving Documents". Explain how vector similarity search works and why these specific chunks were chosen."""),
        ])
        
        samples_str = "\n\n".join([
            f"**Project {s['project']}, Page {s['page']}:**\n```\n{s['content']}...\n```"
            for s in sample_chunks[:3]
        ]) if sample_chunks else "No sample chunks available"
        
        projects_str = ", ".join(projects[:10]) + ("..." if len(projects) > 10 else "")
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=state.user_query,
                route=route,
                project_db="Yes" if data_sources.get("project_db", True) else "No",
                code_db="Yes" if data_sources.get("code_db", False) else "No",
                coop_db="Yes" if data_sources.get("coop_manual", False) else "No",
                retrieved_count=retrieved_count,
                code_count=code_count,
                coop_count=coop_count,
                projects=projects_str,
                samples=samples_str
            ))
            return response.content
        except Exception as e:
            # Fallback if LLM fails
            return f"## 📚 Retrieving Documents\n\n**Search Results:**\n- Project documents: {retrieved_count}\n- Code documents: {code_count}\n- Coop documents: {coop_count}\n- Projects found: {len(projects)}\n\n**Projects:** {projects_str}"
    
    def _explain_grading(self, state: NodeExecutionState) -> str:
        """Use LLM to explain grading/relevance filtering"""
        retrieved_count = state.inputs.get("retrieved_count", 0)
        graded_count = state.outputs.get("graded_count", 0)
        filtered_out = state.outputs.get("filtered_out", 0)
        code_graded = state.outputs.get("code_graded", 0)
        coop_graded = state.outputs.get("coop_graded", 0)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining the document relevance grading process.
Explain:
1. How many documents were evaluated
2. How many passed the relevance check
3. Why documents were filtered out
4. What criteria were used

Be specific about the filtering process. Use markdown formatting. Be conversational."""),
            ("user", """User Query: "{query}"

Grading Results:
- Documents evaluated: {retrieved_count}
- Documents that passed: {graded_count}
- Code documents graded: {code_graded}
- Coop documents graded: {coop_graded}
- Documents filtered out: {filtered_out}

Explain the grading process. Start with "## 🎯 Evaluating Relevance". Explain how relevance scoring works and why some documents were filtered out."""),
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=state.user_query,
                retrieved_count=retrieved_count,
                graded_count=graded_count,
                code_graded=code_graded,
                coop_graded=coop_graded,
                filtered_out=filtered_out
            ))
            return response.content
        except Exception as e:
            # Fallback if LLM fails
            return f"## 🎯 Evaluating Relevance\n\n**Results:**\n- Documents evaluated: {retrieved_count}\n- Documents that passed: {graded_count}\n- Documents filtered out: {filtered_out}"
    
    def _explain_synthesis(self, state: NodeExecutionState) -> str:
        """Use LLM to explain answer synthesis"""
        graded_count = state.inputs.get("graded_docs_count", 0)
        answer_length = state.outputs.get("answer_length", 0)
        citations_count = state.outputs.get("citations_count", 0)
        has_code = state.outputs.get("has_code_answer", False)
        has_coop = state.outputs.get("has_coop_answer", False)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining the answer synthesis process.
Explain:
1. How the answer was generated from documents
2. What sources were used
3. How citations were created
4. The synthesis strategy

Be specific about the process. Use markdown formatting. Be conversational."""),
            ("user", """User Query: "{query}"

Synthesis Results:
- Documents used: {graded_count}
- Answer length: {answer_length} characters
- Citations: {citations_count}
- Code answer included: {has_code}
- Coop answer included: {has_coop}

Explain how the answer was synthesized. Start with "## ✨ Generating Answer". Explain how the LLM combines information from multiple documents to create a coherent answer."""),
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=state.user_query,
                graded_count=graded_count,
                answer_length=answer_length,
                citations_count=citations_count,
                has_code="Yes" if has_code else "No",
                has_coop="Yes" if has_coop else "No"
            ))
            return response.content
        except Exception as e:
            # Fallback if LLM fails
            return f"## ✨ Generating Answer\n\n**Results:**\n- Documents used: {graded_count}\n- Answer length: {answer_length} characters\n- Citations: {citations_count}"



