"""
LLM-based Thinking Log Generator
Generates context-aware, engineer-friendly explanations in real-time
"""
from typing import Dict, Any, Optional
from config.llm_instances import llm_fast
from langchain_core.prompts import ChatPromptTemplate
from config.logging_config import log_query


class IntelligentLogGenerator:
    """
    Generates human-readable, context-aware thinking logs for engineers.
    Adapts explanations based on actual query, execution, and results.
    """
    
    def __init__(self):
        self.llm = llm_fast
    
    def generate_planning_log(
        self,
        query: str,
        plan: Dict[str, Any],
        route: str = "smart",
        project_filter: Optional[str] = None
    ) -> str:
        """
        Generate engineer-friendly explanation of query interpretation and search strategy.
        
        Args:
            query: User's original question
            plan: Query plan with reasoning, steps, subqueries
            route: Data route (smart/large)
            project_filter: Project filter if detected
        """
        reasoning = plan.get('reasoning', '')
        subqueries = plan.get('subqueries', [])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining to a structural engineer how their question will be answered.

Your job is to explain in PLAIN ENGINEERING LANGUAGE:
1. What the engineer is asking for (be specific about what they want)
2. How you interpreted their question
3. What search strategy you'll use and why
4. Any constraints or filters you detected

RULES:
- Use engineering terms: "projects", "drawings", "specifications", "structural elements"
- NO technical jargon: Don't mention "vector search", "embeddings", "nodes", "LLMs"
- Explain decisions: "Since you asked for 5 projects..." or "Because this is about a specific project..."
- Be specific: Use actual project numbers, element types, quantities from the query
- Be concise: 2-4 sentences maximum
- Start with "## 🎯 Understanding Your Question"

EXAMPLES OF GOOD EXPLANATIONS:
- "You're asking for 5 projects that use scissor trusses. Since you didn't specify a project number, I'll search through all past projects and return the 5 most recent ones that mention scissor trusses."
- "You're asking about the foundation details for project 25-01-006. I'll search specifically within that project's drawings and specifications to find foundation-related information."
- "You want to compare roof truss designs across multiple projects. I'll search for projects with different truss types and highlight the key differences in their structural approaches."

EXAMPLES OF BAD EXPLANATIONS:
- "I will use vector similarity search to retrieve relevant documents..." ❌
- "The planner has decomposed your query into subqueries..." ❌
- "I'll execute a hybrid retrieval strategy..." ❌
"""),
            ("user", """Engineer's Question: "{query}"

Search Strategy Reasoning: {reasoning}

Detected Project Filter: {project_filter}

Data Route: {route}

Subqueries Generated: {subqueries}

Generate a clear, engineer-friendly explanation of how you understand their question and how you'll answer it."""),
        ])
        
        subqueries_str = ", ".join([f'"{sq}"' for sq in subqueries[:3]]) if subqueries else "None"
        project_filter_str = project_filter if project_filter else "None (searching all projects)"
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                reasoning=reasoning,
                project_filter=project_filter_str,
                route=route,
                subqueries=subqueries_str
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating planning log: {e}")
            return f"## 🎯 Understanding Your Question\n\n**Your query:** {query}\n\nAnalyzing how best to answer your question..."
    
    def generate_retrieval_log(
        self,
        query: str,
        project_count: int,
        code_count: int,
        coop_count: int,
        projects: list,
        route: str = "smart",
        project_filter: Optional[str] = None
    ) -> str:
        """
        Generate engineer-friendly explanation of document search and results.
        
        Args:
            query: User's original question
            project_count: Number of project documents found
            code_count: Number of code documents found
            coop_count: Number of coop documents found
            projects: List of project keys found
            route: Search route used
            project_filter: Project filter if used
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining to a structural engineer what you found while searching.

Your job is to explain in PLAIN ENGINEERING LANGUAGE:
1. What you were searching for (in engineering terms)
2. What you found (actual project numbers and counts)
3. If you need to sort/limit results, explain why
4. Which databases you searched (projects, code examples, training manuals)

RULES:
- Use engineering terms: "past projects", "design examples", "specifications"
- NO technical jargon: Don't mention "vector database", "embeddings", "similarity scores"
- Be specific: Use actual project numbers if provided
- If many projects found: Explain sorting strategy (by date, relevance, etc.)
- Be concise: 2-4 sentences maximum
- Start with "## 🔍 Searching Through Past Work"

EXAMPLES OF GOOD EXPLANATIONS:
- "Searching through past projects that contain scissor trusses. Found 12 projects: 25-01-006, 25-01-010, 25-01-015, 25-01-022, 25-01-027, 25-01-033, and 6 others. Since you asked for 5, I'll sort by recency and return the 5 most recent."
- "Looking through project 25-01-006 for foundation details. Found 8 relevant drawings and specifications that discuss the foundation design."
- "Searching past projects for examples of moment frames. Found 7 projects with moment frame designs, primarily from commercial building projects."

EXAMPLES OF BAD EXPLANATIONS:
- "Retrieved 50 document chunks from vector store..." ❌
- "Hybrid search returned documents with similarity scores..." ❌
- "Querying Supabase database..." ❌
"""),
            ("user", """Engineer's Question: "{query}"

Search Results:
- Project documents found: {project_count}
- Code examples found: {code_count}
- Training manual sections found: {coop_count}
- Projects: {projects_list}
- Searching in: {search_scope}

Generate a clear explanation of what you searched for and what you found."""),
        ])
        
        # Format projects list
        if projects:
            if len(projects) <= 5:
                projects_list = ", ".join(projects)
            else:
                projects_list = ", ".join(projects[:5]) + f", and {len(projects) - 5} others"
        else:
            projects_list = "None yet"
        
        # Determine search scope
        if project_filter:
            search_scope = f"Project {project_filter} only"
        else:
            search_scope = "All past projects"
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                project_count=project_count,
                code_count=code_count,
                coop_count=coop_count,
                projects_list=projects_list,
                search_scope=search_scope
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating retrieval log: {e}")
            total = project_count + code_count + coop_count
            return f"## 🔍 Searching Through Past Work\n\nFound {total} relevant documents from {len(projects)} projects: {projects_list if projects else 'searching...'}"
    
    def generate_grading_log(
        self,
        query: str,
        retrieved_count: int,
        graded_count: int,
        filtered_out: int
    ) -> str:
        """
        Generate engineer-friendly explanation of relevance filtering.
        
        Args:
            query: User's original question
            retrieved_count: Total documents retrieved
            graded_count: Documents that passed relevance check
            filtered_out: Documents filtered out
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining to a structural engineer how you filtered the search results.

Your job is to explain in PLAIN ENGINEERING LANGUAGE:
1. How you reviewed the documents for relevance
2. What you were looking for specifically
3. How many documents are actually relevant
4. Why some were filtered out (be specific about criteria)

RULES:
- Use engineering terms: "specifications", "design details", "structural information"
- NO technical jargon: Don't mention "relevance scores", "grading", "LLM evaluation"
- Explain the filtering criteria in plain terms
- Be concise: 2-3 sentences maximum
- Start with "## ✅ Filtering Results"

EXAMPLES OF GOOD EXPLANATIONS:
- "Reviewing the 12 projects to confirm they actually use scissor trusses (not just other truss types). All 12 projects confirmed to contain scissor truss designs."
- "Checking the 8 documents to ensure they contain foundation information, not just general project details. Found 6 documents with specific foundation design details, filtered out 2 that only mentioned foundations briefly."
- "Verifying the documents actually discuss moment frame design criteria. Kept 5 detailed design documents, filtered out 3 that only mentioned moment frames in passing."

EXAMPLES OF BAD EXPLANATIONS:
- "Graded documents using relevance scoring algorithm..." ❌
- "LLM evaluated each chunk for semantic relevance..." ❌
- "Applied threshold of 0.7 to filter results..." ❌
"""),
            ("user", """Engineer's Question: "{query}"

Filtering Results:
- Documents reviewed: {retrieved_count}
- Documents with relevant information: {graded_count}
- Documents filtered out: {filtered_out}

Generate a clear explanation of the filtering process."""),
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                retrieved_count=retrieved_count,
                graded_count=graded_count,
                filtered_out=filtered_out
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating grading log: {e}")
            return f"## ✅ Filtering Results\n\nReviewed {retrieved_count} documents. Found {graded_count} with relevant information, filtered out {filtered_out} less relevant documents."
    
    def generate_synthesis_log(
        self,
        query: str,
        graded_count: int,
        projects: list,
        has_code: bool = False,
        has_coop: bool = False
    ) -> str:
        """
        Generate engineer-friendly explanation of answer generation.
        
        Args:
            query: User's original question
            graded_count: Number of documents used
            projects: Project keys used in answer
            has_code: Whether code examples were included
            has_coop: Whether training manual info was included
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are explaining to a structural engineer how you're putting together their answer.

Your job is to explain in PLAIN ENGINEERING LANGUAGE:
1. What information you're using to answer their question
2. Which projects you're drawing from
3. How you're organizing the information
4. Any additional resources you're including (code examples, standards)

RULES:
- Use engineering terms: "project information", "design details", "specifications"
- NO technical jargon: Don't mention "synthesis", "LLM generation", "context window"
- Be specific about which projects you're using
- Be concise: 2-3 sentences maximum
- Start with "## 📋 Preparing Your Answer"

EXAMPLES OF GOOD EXPLANATIONS:
- "Organizing information from 12 projects with scissor trusses, sorted by date to show you the 5 most recent. Including project numbers, key specifications, and design notes for each."
- "Pulling together foundation design details from project 25-01-006, including soil conditions, footing dimensions, and reinforcement details from the structural drawings."
- "Compiling moment frame examples from 7 projects, highlighting the different approaches used in commercial vs. residential buildings. Also including relevant code requirements."

EXAMPLES OF BAD EXPLANATIONS:
- "Synthesizing information from document chunks..." ❌
- "Generating response using LLM with retrieved context..." ❌
- "Combining embeddings to produce coherent answer..." ❌
"""),
            ("user", """Engineer's Question: "{query}"

Information Sources:
- Using information from: {graded_count} documents
- Projects referenced: {projects_list}
- Code examples included: {has_code}
- Standards/training info included: {has_coop}

Generate a clear explanation of how you're preparing the answer."""),
        ])
        
        # Format projects list
        if projects:
            if len(projects) <= 3:
                projects_list = ", ".join(projects)
            else:
                projects_list = ", ".join(projects[:3]) + f", and {len(projects) - 3} others"
        else:
            projects_list = "multiple projects"
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                graded_count=graded_count,
                projects_list=projects_list,
                has_code="Yes" if has_code else "No",
                has_coop="Yes" if has_coop else "No"
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating synthesis log: {e}")
            return f"## 📋 Preparing Your Answer\n\nOrganizing information from {graded_count} relevant documents across {len(projects) if projects else 'multiple'} projects."


# Singleton instance
_log_generator = IntelligentLogGenerator()


def generate_log_from_event(event: Dict[str, Any], query: str) -> Optional[str]:
    """
    Generate a thinking log from a streaming event.
    
    Args:
        event: Event from LangGraph callback
        query: User's original query
        
    Returns:
        Human-readable thinking log or None
    """
    event_type = event.get('type')
    node = event.get('node', '')
    metadata = event.get('metadata', {})
    
    # Node start events
    if event_type == 'node_start':
        if 'plan' in node.lower():
            return f"## 🎯 Analyzing Your Question\n\nLet me understand what you're asking and determine the best way to find the answer..."
        elif 'retrieve' in node.lower():
            return f"## 🔍 Searching\n\nLooking through past projects and documentation..."
        elif 'grade' in node.lower():
            return f"## ✅ Reviewing Results\n\nChecking which documents have the information you need..."
        elif 'answer' in node.lower() or 'synth' in node.lower():
            return f"## 📋 Preparing Answer\n\nOrganizing the information I found..."
    
    # Node end events - generate detailed logs
    elif event_type == 'node_end':
        if 'plan' in node.lower() and metadata.get('plan'):
            plan_data = metadata.get('plan', {})
            route = metadata.get('route', 'smart')
            project_filter = metadata.get('project_filter')
            return _log_generator.generate_planning_log(
                query=query,
                plan=plan_data,
                route=route,
                project_filter=project_filter
            )
        
        elif 'retrieve' in node.lower() and metadata.get('retrieval'):
            retrieval_data = metadata.get('retrieval', {})
            return _log_generator.generate_retrieval_log(
                query=query,
                project_count=retrieval_data.get('project_count', 0),
                code_count=retrieval_data.get('code_count', 0),
                coop_count=retrieval_data.get('coop_count', 0),
                projects=retrieval_data.get('projects', []),
                route=metadata.get('route', 'smart'),
                project_filter=metadata.get('project_filter')
            )
        
        elif 'grade' in node.lower() and metadata.get('grading'):
            grading_data = metadata.get('grading', {})
            return _log_generator.generate_grading_log(
                query=query,
                retrieved_count=grading_data.get('retrieved_count', 0),
                graded_count=grading_data.get('graded_count', 0),
                filtered_out=grading_data.get('filtered_out', 0)
            )
        
        elif ('answer' in node.lower() or 'synth' in node.lower()) and metadata.get('synthesis'):
            synthesis_data = metadata.get('synthesis', {})
            return _log_generator.generate_synthesis_log(
                query=query,
                graded_count=synthesis_data.get('citations_count', 0),
                projects=metadata.get('projects', []),
                has_code=metadata.get('has_code', False),
                has_coop=metadata.get('has_coop', False)
            )
    
    return None

