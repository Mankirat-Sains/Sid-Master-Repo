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
        Generate planning log using the planner's reasoning directly (no LLM call).
        
        Args:
            query: User's original question
            plan: Query plan with reasoning, steps, subqueries
            route: Data route (smart/large)
            project_filter: Project filter if detected
        """
        reasoning = plan.get('reasoning', '')
        
        # Use the planner's reasoning directly - it's already perfect
        if reasoning:
            return f"QUERY ANALYSIS\n\n{reasoning}"
        else:
            return f"QUERY ANALYSIS\n\nAnalyzing query to determine optimal search strategy and document sources."
    
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
            ("system", """You are providing a concise, factual summary of document retrieval results to a structural engineer.

CRITICAL RULES - ANTI-HALLUCINATION:
- Report ONLY the exact data provided (counts and project numbers)
- DO NOT invent or assume document contents you haven't seen
- DO NOT invent specific beam sizes, dimensions, or technical details
- DO NOT elaborate beyond what the data shows
- If project numbers are provided, list them. If not, say "projects not yet identified"
- State counts and scope ONLY - no speculation about document quality or contents

Your job:
1. Report document counts clearly
2. List actual project numbers provided (all of them if 10 or fewer, first 5 + "and X others" if more)
3. State what was searched for (based on the query)
4. Keep to 2-3 sentences maximum

FORMATTING:
- Header: "DOCUMENT RETRIEVAL SUMMARY"
- Be direct and factual
- NO emojis
- NO technical implementation details

GOOD EXAMPLE:
"DOCUMENT RETRIEVAL SUMMARY

Retrieved 100 project documents and 100 code examples for steel beam design. Projects identified: 25-01-005, 25-01-012, 25-01-036, 25-01-044, 25-01-060, and 15 others. Documents selected based on relevance to steel beam design criteria."

BAD EXAMPLE (inventing details):
"Retrieved documents containing W16x31 beam specifications..." ❌ (you don't know this)
"Project 25-01-006 shows detailed connection details..." ❌ (you haven't seen the documents)"""),
            ("user", """Query: "{query}"

ACTUAL DATA PROVIDED:
- Project documents: {project_count}
- Code examples: {code_count}
- Training materials: {coop_count}
- Project numbers: {projects_list}
- Scope: {search_scope}

Report ONLY this factual data. 2-3 sentences maximum."""),
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
            projects_str = f"from {len(projects)} projects: {projects_list}" if projects else "from multiple project sources"
            return f"DOCUMENT RETRIEVAL SUMMARY\n\nRetrieved {total} technical documents {projects_str}. Documents include structural drawings, design calculations, and specification sheets relevant to the query parameters."
    
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
            ("system", """You are providing a concise, factual summary of document filtering results to a structural engineer.

CRITICAL RULES - ANTI-HALLUCINATION:
- Report ONLY the exact counts provided
- DO NOT invent reasons why documents were kept or filtered
- DO NOT assume or describe document contents you haven't seen
- DO NOT invent technical details about what documents contain
- State counts and percentages ONLY

Your job:
1. Report how many documents were reviewed
2. Report how many passed relevance criteria with percentage
3. Report how many were filtered out
4. State general criteria used (relevance to the query topic)
5. Keep to 2-3 sentences maximum

FORMATTING:
- Header: "RELEVANCE ASSESSMENT"
- Be direct and factual
- NO emojis
- NO invented examples

GOOD EXAMPLE:
"RELEVANCE ASSESSMENT

Reviewed 100 documents for relevance to steel beam design. Retained 100 documents (100% pass rate) that met relevance criteria. No documents were filtered out."

BAD EXAMPLE (inventing details):
"Filtered out documents lacking W-section specifications..." ❌ (you don't know this)
"Kept documents with load calculations showing DL + LL..." ❌ (you haven't seen the documents)"""),
            ("user", """Query: "{query}"

ACTUAL DATA PROVIDED:
- Documents reviewed: {retrieved_count}
- Documents retained: {graded_count}
- Documents filtered: {filtered_out}

Report ONLY this factual data. 2-3 sentences maximum."""),
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
            percent = round((graded_count / retrieved_count * 100)) if retrieved_count > 0 else 0
            return f"RELEVANCE ASSESSMENT\n\nReviewed {retrieved_count} technical documents for relevance to query criteria. Retained {graded_count} documents ({percent}%) that met technical requirements including complete design information, material specifications, and applicable code references. Filtered {filtered_out} documents that lacked sufficient technical detail or direct applicability."
    
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
            ("system", """You are providing a concise, factual summary of information compilation to a structural engineer.

CRITICAL RULES - ANTI-HALLUCINATION:
- Report ONLY the exact data provided (document counts and project numbers)
- DO NOT invent or describe what information will be extracted
- DO NOT assume document contents or organization strategies
- DO NOT invent specific technical details, beam sizes, or code sections
- If project numbers are provided, list them. If not, say "multiple projects"
- State counts and sources ONLY

Your job:
1. Report how many documents are being used
2. List actual project numbers provided (all if 10 or fewer, first 5 + "and X others" if more)
3. Note if code examples or training materials are included
4. Keep to 2-3 sentences maximum

FORMATTING:
- Header: "INFORMATION COMPILATION"
- Be direct and factual
- NO emojis
- NO invented details about content or organization

GOOD EXAMPLE:
"INFORMATION COMPILATION

Compiling information from 100 documents across 15 projects including 30-02-001, 30-02-015, 30-02-027, 30-02-033, 30-02-045, and 10 others. Including code examples and training materials to provide comprehensive guidance."

BAD EXAMPLE (inventing details):
"Extracting W-section beam schedules, load calculations..." ❌ (you haven't seen the documents)
"Organizing by span ranges of 10-20ft, 20-30ft..." ❌ (you don't know the organization)
"Including AISC 360 Chapter F provisions..." ❌ (you don't know what's in the docs)"""),
            ("user", """Query: "{query}"

ACTUAL DATA PROVIDED:
- Documents: {graded_count}
- Projects: {projects_list}
- Code examples: {has_code}
- Training materials: {has_coop}

Report ONLY this factual data. 2-3 sentences maximum."""),
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
            proj_str = f"{len(projects)} projects: {projects_list if len(projects) <= 5 else ', '.join(projects[:5]) + f' and {len(projects)-5} others'}" if projects else "multiple project sources"
            return f"INFORMATION COMPILATION\n\nCompiling technical information from {graded_count} engineering documents across {proj_str}. Extracting design details, calculations, specifications, and practical implementation examples to provide comprehensive response to query requirements."
    
    def generate_router_dispatcher_log(
        self,
        query: str,
        selected_routers: list
    ) -> str:
        """
        Generate log for router dispatcher node.
        
        Args:
            query: User's original question
            selected_routers: List of routers selected (e.g., ["rag", "web", "desktop"])
        """
        if not selected_routers:
            return "ROUTER SELECTION\n\nAnalyzing query to determine appropriate data sources and tools."
        
        router_names = {
            "rag": "document database",
            "web": "web calculation tools",
            "desktop": "desktop applications"
        }
        
        router_descriptions = [router_names.get(r, r) for r in selected_routers]
        
        if len(router_descriptions) == 1:
            return f"ROUTER SELECTION\n\nSelected {router_descriptions[0]} to process this query."
        else:
            router_list = ", ".join(router_descriptions[:-1]) + f", and {router_descriptions[-1]}"
            return f"ROUTER SELECTION\n\nSelected multiple tools: {router_list} to process this query in parallel."
    
    def generate_rag_log(
        self,
        query: str,
        query_plan: Optional[Dict] = None,
        data_route: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> str:
        """
        Generate log for RAG wrapper node.
        
        Args:
            query: User's original question
            query_plan: Query plan from rag_plan
            data_route: Data route (smart/large)
            data_sources: Selected data sources
        """
        if query_plan:
            steps = query_plan.get("steps", [])
            if steps:
                return f"QUERY PLANNING\n\nDecomposed query into {len(steps)} execution steps. Analyzing query structure and determining optimal search strategy."
        
        route_desc = "optimized search" if data_route == "smart" else "comprehensive search"
        return f"QUERY PLANNING\n\nPreparing {route_desc} strategy based on query complexity and available data sources."
    
    def generate_verify_log(
        self,
        query: str,
        needs_fix: bool = False,
        follow_up_count: int = 0,
        suggestion_count: int = 0
    ) -> str:
        """
        Generate log for verification node.
        
        Args:
            query: User's original question
            needs_fix: Whether answer needs correction
            follow_up_count: Number of follow-up questions generated
            suggestion_count: Number of follow-up suggestions generated
        """
        if needs_fix:
            return "QUALITY VERIFICATION\n\nAnswer quality check identified areas requiring improvement. Initiating corrective retrieval to enhance response accuracy."
        
        follow_up_text = ""
        if follow_up_count > 0 or suggestion_count > 0:
            parts = []
            if follow_up_count > 0:
                parts.append(f"{follow_up_count} follow-up question{'s' if follow_up_count != 1 else ''}")
            if suggestion_count > 0:
                parts.append(f"{suggestion_count} suggestion{'s' if suggestion_count != 1 else ''}")
            follow_up_text = f" Generated {', '.join(parts)} to help explore related topics."
        
        return f"QUALITY VERIFICATION\n\nVerified answer quality and completeness against retrieved documents.{follow_up_text}"
    
    def generate_correct_log(
        self,
        query: str,
        support_score: float = 1.0,
        corrective_attempted: bool = False
    ) -> str:
        """
        Generate log for correction node.
        
        Args:
            query: User's original question
            support_score: Answer support score (0.0-1.0)
            corrective_attempted: Whether correction was attempted
        """
        if corrective_attempted:
            score_pct = int(support_score * 100)
            return f"ANSWER FINALIZATION\n\nFinalized answer with {score_pct}% support score based on document evidence. Answer is ready for delivery."
        
        return "ANSWER FINALIZATION\n\nFinalizing answer and preparing for delivery."
    
    def generate_image_embeddings_log(
        self,
        query: str,
        image_count: int
    ) -> str:
        """
        Generate log for image embedding generation.
        
        Args:
            query: User's original question
            image_count: Number of images being processed
        """
        if image_count == 1:
            return "IMAGE PROCESSING\n\nGenerating embedding for uploaded image to enable similarity search."
        else:
            return f"IMAGE PROCESSING\n\nGenerating embeddings for {image_count} uploaded images to enable similarity search."
    
    def generate_image_similarity_log(
        self,
        query: str,
        result_count: int,
        project_count: int = 0
    ) -> str:
        """
        Generate log for image similarity search.
        
        Args:
            query: User's original question
            result_count: Number of similar images found
            project_count: Number of unique projects in results
        """
        if result_count == 0:
            return "IMAGE SIMILARITY SEARCH\n\nNo similar images found in database. Proceeding with text-based search."
        
        if project_count > 0:
            return f"IMAGE SIMILARITY SEARCH\n\nFound {result_count} similar image{'s' if result_count != 1 else ''} from {project_count} project{'s' if project_count != 1 else ''}. These will be included in the search results."
        else:
            return f"IMAGE SIMILARITY SEARCH\n\nFound {result_count} similar image{'s' if result_count != 1 else ''}. These will be included in the search results."


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

