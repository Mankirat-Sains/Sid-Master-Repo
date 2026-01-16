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
        project_filter: Optional[str] = None,
        query_plan: Optional[Dict] = None
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
            query_plan: Optional query plan with steps/subqueries
        """
        # Extract technical context from query plan if available
        search_terms = []
        technical_context = ""
        if query_plan:
            steps = query_plan.get("steps", [])
            subqueries = query_plan.get("subqueries", [])
            if subqueries:
                search_terms = [sq.get("query", "") for sq in subqueries if isinstance(sq, dict)]
            elif steps:
                # Extract search terms from step descriptions
                for step in steps:
                    if isinstance(step, dict) and "query" in step:
                        search_terms.append(step["query"])
                    elif isinstance(step, str):
                        search_terms.append(step)
            
            if search_terms:
                technical_context = f"Search terms: {', '.join(search_terms[:3])}" + (f" and {len(search_terms)-3} more" if len(search_terms) > 3 else "")
        
        # Extract engineering concepts from the query itself
        engineering_keywords = []
        query_lower = query.lower()
        common_terms = ["slab", "beam", "column", "foundation", "truss", "connection", "reinforcement", "concrete", "steel", "timber", "design", "specification", "detail", "drawing", "calculation"]
        for term in common_terms:
            if term in query_lower:
                engineering_keywords.append(term)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are providing a concise, engineer-focused summary of document retrieval to a structural engineer.

CRITICAL RULES - FACTUAL REPORTING:
- Report the exact counts and project numbers provided
- Explain what engineering task is being performed based on the query
- Describe the search strategy in engineering terms (e.g., "searching for floating slab specifications")
- DO NOT invent specific document contents (beam sizes, dimensions, etc.)
- DO NOT claim to know what's inside documents you haven't seen
- Focus on the ENGINEERING CONTEXT: what the system is searching for and why

Your job:
1. Explain the engineering task being performed (based on the query keywords)
2. Report document counts and project numbers
3. Describe the search scope and strategy
4. Use engineering terminology naturally
5. Keep to 3-4 sentences

FORMATTING:
- Header: "DOCUMENT RETRIEVAL SUMMARY"
- Use engineering language (e.g., "specifications", "design details", "structural elements")
- Be informative but factual
- NO emojis

GOOD EXAMPLE:
"DOCUMENT RETRIEVAL SUMMARY

Searching past projects for floating slab design specifications and construction details. Retrieved 50 project documents and 0 code examples from 50 unique projects including 25-01-005, 25-01-012, 25-01-036, 25-01-044, 25-01-060, and 45 others. Documents were selected based on semantic similarity to the query terms and relevance to slab-on-grade construction methods."

BAD EXAMPLE (inventing details):
"Retrieved documents containing 6-inch slab thickness specifications..." ❌ (you don't know this)
"Project 25-01-006 shows detailed rebar spacing of #4@12"..." ❌ (you haven't seen the documents)"""),
            ("user", """Query: "{query}"
{technical_context}
{engineering_keywords}

ACTUAL DATA PROVIDED:
- Project documents: {project_count}
- Code examples: {code_count}
- Training materials: {coop_count}
- Project numbers: {projects_list}
- Search scope: {search_scope}
- Search route: {route} ({route_desc})

Generate an engineer-focused summary explaining what engineering information is being searched for and the results."""),
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
        
        # Format technical context
        tech_context_str = technical_context if technical_context else ""
        eng_keywords_str = f"Engineering concepts identified: {', '.join(engineering_keywords)}" if engineering_keywords else ""
        route_desc = "optimized semantic search" if route == "smart" else "comprehensive page-level search"
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                technical_context=tech_context_str,
                engineering_keywords=eng_keywords_str,
                project_count=project_count,
                code_count=code_count,
                coop_count=coop_count,
                projects_list=projects_list,
                search_scope=search_scope,
                route=route,
                route_desc=route_desc
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating retrieval log: {e}")
            total = project_count + code_count + coop_count
            projects_str = f"from {len(projects)} projects: {projects_list}" if projects else "from multiple project sources"
            eng_task = "engineering information" if not engineering_keywords else f"{', '.join(engineering_keywords)} design information"
            return f"DOCUMENT RETRIEVAL SUMMARY\n\nSearching past projects for {eng_task} related to the query. Retrieved {total} technical documents {projects_str} using {route_desc}. Documents include structural drawings, design calculations, and specification sheets relevant to the query parameters."
    
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
        # Extract engineering concepts from query
        query_lower = query.lower()
        engineering_focus = []
        if any(term in query_lower for term in ["slab", "foundation", "footing"]):
            engineering_focus.append("foundation systems")
        if any(term in query_lower for term in ["beam", "girder", "joist"]):
            engineering_focus.append("structural framing")
        if any(term in query_lower for term in ["column", "post", "pier"]):
            engineering_focus.append("vertical elements")
        if any(term in query_lower for term in ["connection", "joint", "detail"]):
            engineering_focus.append("connection details")
        if any(term in query_lower for term in ["reinforcement", "rebar", "steel"]):
            engineering_focus.append("reinforcement details")
        
        focus_text = ", ".join(engineering_focus) if engineering_focus else "the query topic"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are providing a concise, engineer-focused summary of document relevance filtering to a structural engineer.

CRITICAL RULES - FACTUAL REPORTING:
- Report the exact counts and percentages provided
- Explain the relevance assessment process in engineering terms
- Describe what criteria were used (relevance to engineering concepts in the query)
- DO NOT invent specific reasons why individual documents were kept/filtered
- DO NOT claim to know document contents you haven't seen
- Focus on the ENGINEERING CONTEXT: what makes documents relevant

Your job:
1. Explain what engineering information is being assessed for relevance
2. Report how many documents were reviewed and retained
3. Explain the relevance criteria in engineering terms
4. Use engineering language naturally
5. Keep to 3-4 sentences

FORMATTING:
- Header: "RELEVANCE ASSESSMENT"
- Use engineering terminology
- Be informative but factual
- NO emojis

GOOD EXAMPLE:
"RELEVANCE ASSESSMENT

Assessing 100 retrieved documents for relevance to floating slab design specifications and construction methods. Retained 100 documents (100% pass rate) that contain information directly related to slab-on-grade systems, foundation details, and related structural elements. No documents were filtered out, indicating strong alignment between the query and retrieved content."

BAD EXAMPLE (inventing details):
"Filtered out documents lacking 6-inch slab thickness specifications..." ❌ (you don't know this)
"Kept documents with rebar spacing details..." ❌ (you haven't seen the documents)"""),
            ("user", """Query: "{query}"

ACTUAL DATA PROVIDED:
- Documents reviewed: {retrieved_count}
- Documents retained: {graded_count}
- Documents filtered: {filtered_out}
- Engineering focus: {engineering_focus}

Generate an engineer-focused summary explaining the relevance assessment process and results."""),
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages(
                query=query,
                retrieved_count=retrieved_count,
                graded_count=graded_count,
                filtered_out=filtered_out,
                engineering_focus=focus_text
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating grading log: {e}")
            percent = round((graded_count / retrieved_count * 100)) if retrieved_count > 0 else 0
            return f"RELEVANCE ASSESSMENT\n\nAssessing {retrieved_count} retrieved documents for relevance to {focus_text}. Retained {graded_count} documents ({percent}% pass rate) that contain information directly related to the engineering concepts in the query. Filtered {filtered_out} documents that lacked sufficient technical detail or direct applicability to the query requirements."
    
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
        # Extract engineering task from query
        query_lower = query.lower()
        task_description = []
        if any(term in query_lower for term in ["specification", "spec", "requirement"]):
            task_description.append("design specifications")
        if any(term in query_lower for term in ["detail", "drawing", "plan"]):
            task_description.append("construction details")
        if any(term in query_lower for term in ["calculation", "calc", "design"]):
            task_description.append("design calculations")
        if any(term in query_lower for term in ["method", "approach", "technique"]):
            task_description.append("design methods")
        
        task_text = ", ".join(task_description) if task_description else "engineering information"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are providing a concise, engineer-focused summary of information compilation to a structural engineer.

CRITICAL RULES - FACTUAL REPORTING:
- Report the exact document counts and project numbers provided
- Explain what engineering information is being compiled
- Describe the compilation process in engineering terms
- DO NOT invent specific details about what will be extracted
- DO NOT assume document organization or content structure
- DO NOT claim to know specific technical values (sizes, dimensions, etc.)
- Focus on the ENGINEERING CONTEXT: what types of information are being synthesized

Your job:
1. Explain what engineering information is being compiled (based on query)
2. Report document counts and project sources
3. Note if code examples or training materials are included
4. Use engineering terminology naturally
5. Keep to 3-4 sentences

FORMATTING:
- Header: "INFORMATION COMPILATION"
- Use engineering language (e.g., "design specifications", "construction details")
- Be informative but factual
- NO emojis

GOOD EXAMPLE:
"INFORMATION COMPILATION

Compiling design specifications and construction details from 100 relevant documents across 15 projects including 30-02-001, 30-02-015, 30-02-027, 30-02-033, 30-02-045, and 10 others. Synthesizing information from project drawings, design calculations, and specification sheets. Including code examples and training materials to provide comprehensive guidance on design requirements and construction methods."

BAD EXAMPLE (inventing details):
"Extracting W16x31 beam schedules with load calculations..." ❌ (you haven't seen the documents)
"Organizing by span ranges of 10-20ft..." ❌ (you don't know the organization)
"Including AISC 360 Chapter F provisions..." ❌ (you don't know what's in the docs)"""),
            ("user", """Query: "{query}"

ACTUAL DATA PROVIDED:
- Documents: {graded_count}
- Projects: {projects_list}
- Code examples: {has_code}
- Training materials: {has_coop}
- Engineering task: {task_description}

Generate an engineer-focused summary explaining what engineering information is being compiled and from which sources."""),
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
                has_coop="Yes" if has_coop else "No",
                task_description=task_text
            ))
            return response.content.strip()
        except Exception as e:
            log_query.error(f"Error generating synthesis log: {e}")
            proj_str = f"{len(projects)} projects: {projects_list if len(projects) <= 5 else ', '.join(projects[:5]) + f' and {len(projects)-5} others'}" if projects else "multiple project sources"
            sources_text = []
            if has_code:
                sources_text.append("code examples")
            if has_coop:
                sources_text.append("training materials")
            sources_str = f" Including {', '.join(sources_text)}." if sources_text else ""
            return f"INFORMATION COMPILATION\n\nCompiling {task_text} from {graded_count} relevant engineering documents across {proj_str}. Synthesizing information from project drawings, design calculations, and specification sheets to provide comprehensive response.{sources_str}"
    
    def generate_router_dispatcher_log(
        self,
        query: str,
        selected_routers: list
    ) -> str:
        """
        Generate log for router dispatcher node.
        
        Args:
            query: User's original question
            selected_routers: List of routers selected (e.g., ["database", "web", "desktop"])
        """
        if not selected_routers:
            return "ROUTER SELECTION\n\nAnalyzing query to determine appropriate data sources and engineering tools."
        
        # Extract engineering context from query
        query_lower = query.lower()
        needs_docs = any(term in query_lower for term in ["past project", "previous", "similar", "example", "specification", "detail", "drawing"])
        needs_calc = any(term in query_lower for term in ["calculate", "design", "size", "dimension", "load"])
        
        router_names = {
            "database": "project document database",
            "rag": "project document database",  # Legacy support
            "web": "web-based calculation tools",
            "desktop": "desktop engineering applications"
        }
        
        router_descriptions = [router_names.get(r, r) for r in selected_routers]
        
        # Generate context-aware message
        if len(router_descriptions) == 1:
            router_desc = router_descriptions[0]
            if "database" in selected_routers or "rag" in selected_routers:  # Support legacy "rag"
                context = "searching past project documents and design specifications"
            elif "web" in selected_routers:
                context = "performing calculations using web-based tools"
            elif "desktop" in selected_routers:
                context = "accessing desktop engineering applications"
            else:
                context = "processing this engineering query"
            return f"ROUTER SELECTION\n\nSelected {router_desc} for {context}."
        else:
            router_list = ", ".join(router_descriptions[:-1]) + f", and {router_descriptions[-1]}"
            return f"ROUTER SELECTION\n\nSelected multiple tools: {router_list} to process this query in parallel, enabling comprehensive engineering analysis."
    
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
        # Extract engineering context
        query_lower = query.lower()
        engineering_focus = []
        if any(term in query_lower for term in ["slab", "foundation", "footing"]):
            engineering_focus.append("foundation systems")
        if any(term in query_lower for term in ["beam", "girder", "framing"]):
            engineering_focus.append("structural framing")
        if any(term in query_lower for term in ["connection", "joint", "detail"]):
            engineering_focus.append("connection details")
        
        focus_text = f" for {', '.join(engineering_focus)}" if engineering_focus else ""
        
        if query_plan:
            steps = query_plan.get("steps", [])
            subqueries = query_plan.get("subqueries", [])
            if steps:
                step_desc = f"{len(steps)} search steps" if len(steps) > 1 else "a structured search approach"
                return f"QUERY PLANNING\n\nDecomposed engineering query into {step_desc}{focus_text}. Analyzing query structure and determining optimal search strategy across project documents and design specifications."
            elif subqueries:
                return f"QUERY PLANNING\n\nPreparing multi-faceted search strategy{focus_text} with {len(subqueries)} targeted subqueries to comprehensively address the engineering question."
        
        route_desc = "optimized semantic search" if data_route == "smart" else "comprehensive page-level search"
        data_sources_desc = []
        if data_sources:
            if data_sources.get("project_db"):
                data_sources_desc.append("project documents")
            if data_sources.get("code_db"):
                data_sources_desc.append("code examples")
            if data_sources.get("coop_manual"):
                data_sources_desc.append("training materials")
        
        sources_text = f" across {', '.join(data_sources_desc)}" if data_sources_desc else ""
        return f"QUERY PLANNING\n\nPreparing {route_desc} strategy{focus_text}{sources_text} based on query complexity and engineering requirements."
    
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
        # Extract engineering context from query
        query_lower = query.lower()
        engineering_focus = []
        if any(term in query_lower for term in ["specification", "requirement", "standard"]):
            engineering_focus.append("design requirements")
        if any(term in query_lower for term in ["detail", "drawing", "plan"]):
            engineering_focus.append("construction details")
        if any(term in query_lower for term in ["calculation", "design", "method"]):
            engineering_focus.append("design methods")
        
        focus_text = f" for {', '.join(engineering_focus)}" if engineering_focus else ""
        
        if needs_fix:
            return f"QUALITY VERIFICATION\n\nAnswer quality assessment identified gaps{focus_text} that require additional information. Initiating corrective retrieval to enhance response accuracy and completeness with more relevant engineering documents."
        
        follow_up_text = ""
        if follow_up_count > 0 or suggestion_count > 0:
            parts = []
            if follow_up_count > 0:
                parts.append(f"{follow_up_count} follow-up question{'s' if follow_up_count != 1 else ''}")
            if suggestion_count > 0:
                parts.append(f"{suggestion_count} suggestion{'s' if suggestion_count != 1 else ''}")
            follow_up_text = f" Generated {', '.join(parts)} to help explore related engineering topics and design considerations."
        
        return f"QUALITY VERIFICATION\n\nVerified answer quality and completeness against retrieved engineering documents{focus_text}. Confirmed that the response addresses the query requirements with appropriate technical detail.{follow_up_text}"
    
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
        # Extract engineering context
        query_lower = query.lower()
        engineering_focus = []
        if any(term in query_lower for term in ["specification", "requirement"]):
            engineering_focus.append("design specifications")
        if any(term in query_lower for term in ["detail", "drawing"]):
            engineering_focus.append("construction details")
        
        focus_text = f" covering {', '.join(engineering_focus)}" if engineering_focus else ""
        
        if corrective_attempted:
            score_pct = int(support_score * 100)
            if score_pct >= 90:
                quality_desc = "high confidence"
            elif score_pct >= 70:
                quality_desc = "good confidence"
            else:
                quality_desc = "moderate confidence"
            return f"ANSWER FINALIZATION\n\nFinalized engineering answer{focus_text} with {score_pct}% document support ({quality_desc}). The response is based on verified project documents and design specifications, ready for delivery."
        
        return f"ANSWER FINALIZATION\n\nFinalizing engineering answer{focus_text} and preparing for delivery. Synthesizing information from verified project documents and design specifications."
    
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
        # Extract engineering context from query
        query_lower = query.lower()
        image_type = []
        if any(term in query_lower for term in ["drawing", "plan", "detail", "section"]):
            image_type.append("drawings")
        if any(term in query_lower for term in ["photo", "image", "picture"]):
            image_type.append("images")
        
        type_text = f" ({', '.join(image_type)})" if image_type else ""
        
        if image_count == 1:
            return f"IMAGE PROCESSING\n\nProcessing uploaded image{type_text} to extract visual features and enable similarity search across past project drawings and design documents."
        else:
            return f"IMAGE PROCESSING\n\nProcessing {image_count} uploaded images{type_text} to extract visual features and enable similarity search across past project drawings and design documents."
    
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
        # Extract engineering context
        query_lower = query.lower()
        image_type = "drawings" if any(term in query_lower for term in ["drawing", "plan", "detail", "section"]) else "images"
        
        if result_count == 0:
            return f"IMAGE SIMILARITY SEARCH\n\nNo similar {image_type} found in the project database matching the uploaded image. Proceeding with text-based semantic search to find relevant design documents and specifications."
        
        if project_count > 0:
            return f"IMAGE SIMILARITY SEARCH\n\nFound {result_count} similar {image_type} from {project_count} past project{'s' if project_count != 1 else ''} with matching visual features. These related drawings and design documents will be included in the search results to provide comprehensive engineering context."
        else:
            return f"IMAGE SIMILARITY SEARCH\n\nFound {result_count} similar {image_type} with matching visual features. These related drawings and design documents will be included in the search results to provide comprehensive engineering context."


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

