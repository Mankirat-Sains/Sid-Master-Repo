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
            ("system", """You are providing a detailed technical analysis to a structural engineer explaining how their query will be processed.

Your job is to provide a COMPREHENSIVE TECHNICAL EXPLANATION including:
1. Precise interpretation of what the engineer is requesting (specific elements, quantities, design criteria)
2. Detailed search strategy including document types that will be examined (structural drawings, specifications, detail sheets, calculations)
3. Specific search terms and why they were selected based on engineering terminology
4. Expected document locations within projects (title blocks, general notes, structural details, foundation plans, etc.)
5. Any project-specific constraints or filters that will narrow the search scope
6. Estimated scope of the search (number of projects, document types, time periods if relevant)

FORMATTING AND STYLE REQUIREMENTS:
- Use professional section header: "QUERY ANALYSIS"
- Write in complete, technical paragraphs (4-6 sentences minimum)
- Use precise engineering terminology: beam sections (W16x31), load types (dead load, live load), design elements (moment frames, shear walls)
- Include specific project numbers when filtering is applied
- Explain the engineering rationale behind search decisions
- Reference actual search terms that will be used (e.g., "searching for 'steel beam', 'W-section', 'AISC', 'beam schedule'")
- NO emojis or casual language
- NO mentions of "vector search", "embeddings", "nodes", "LLMs", or other technical implementation details

EXAMPLE OF GOOD TECHNICAL EXPLANATION:
"QUERY ANALYSIS

The query requests detailed information on steel beam design, specifically requiring guidance on load calculations, span capabilities, and material specifications. The search will target structural engineering documents from past projects that demonstrate successful steel beam applications in various contexts. Search terms will include 'steel beam', 'W-section', 'wide flange', 'beam schedule', 'load calculations', and 'AISC specifications' to ensure comprehensive coverage of relevant documentation.

The system will examine structural drawings (specifically beam schedules and framing plans), design calculations showing load analysis, and specification sheets detailing material properties and connection requirements. Given the broad scope of the query without project-specific constraints, the search will span approximately 20-30 recent projects to provide a representative sample of design approaches and methodologies. Documents will be prioritized based on the presence of detailed design calculations, material specifications, and practical implementation details that demonstrate code-compliant design practices."

AVOID:
- Generic statements like "I'll search for relevant information"
- Vague descriptions without specific document types
- References to technical implementation methods
- Emoji or casual formatting"""),
            ("user", """Engineer's Question: "{query}"

Search Strategy Reasoning: {reasoning}

Detected Project Filter: {project_filter}

Data Route: {route}

Search Terms Generated: {subqueries}

Provide a comprehensive technical analysis of how this query will be processed, including specific document types, search terms, and expected information sources."""),
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
            return f"QUERY ANALYSIS\n\nAnalyzing query: {query}\n\nDetermining optimal search strategy and document sources for this technical inquiry."
    
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
            ("system", """You are providing a detailed technical summary to a structural engineer of the document retrieval results.

Your job is to provide a COMPREHENSIVE RETRIEVAL REPORT including:
1. Specific description of what was searched for in technical terms
2. Complete list of project numbers found (list ALL projects by number if 10 or fewer, summarize if more)
3. Types of documents retrieved from each source (structural drawings, calculations, specifications, detail sheets)
4. Breakdown of document counts by category with brief descriptions of content
5. Relevance explanation: why these specific projects were selected and what makes them applicable
6. If multiple projects found: sorting/prioritization strategy being used
7. Any notable patterns in the results (common design approaches, specific firms, time periods)

FORMATTING AND STYLE REQUIREMENTS:
- Use professional section header: "DOCUMENT RETRIEVAL SUMMARY"
- Write in detailed, technical paragraphs (5-7 sentences minimum)
- List ALL project numbers when 10 or fewer projects (format: "Projects identified: 25-01-006, 25-01-017, 25-01-022...")
- For each data source, specify document types: "project documents (100 structural drawings and specifications)", "code examples (50 design calculation sheets)", "training materials (25 reference sections)"
- Explain WHY each project is relevant (e.g., "Project 25-01-006 contains W-section beam designs with similar span requirements")
- Include information about document quality and completeness
- Reference specific drawing types: "foundation plans", "framing elevations", "structural details", "beam schedules"
- NO emojis or casual language
- NO mentions of technical implementation details

EXAMPLE OF GOOD TECHNICAL RETRIEVAL SUMMARY:
"DOCUMENT RETRIEVAL SUMMARY

The search for steel beam design guidance has identified 100 project documents and 100 code reference examples containing relevant structural information. Projects identified include: 25-01-006, 25-01-017, 25-01-022, 25-01-038, 25-01-045, 25-01-052, 25-01-063, 25-01-071, 25-01-084, and 91 additional projects. These projects were selected based on the presence of steel beam design elements, including W-section specifications, load calculations, and connection details.

From the project database, retrieved documents include structural drawings showing beam schedules and framing plans, design calculations demonstrating load analysis and member sizing, and specification sheets detailing material properties (ASTM A992 steel) and welding/bolting requirements. The code example database provided 100 reference documents containing AISC design procedures, load combination examples, and connection design calculations. Given the substantial number of results, documents will be prioritized based on the completeness of design information, presence of detailed calculations, and clarity of material specifications to ensure the most useful examples are presented first."

AVOID:
- Generic counts without context
- Vague descriptions like "found some projects"
- Missing project numbers when available
- No explanation of relevance or document types"""),
            ("user", """Engineer's Question: "{query}"

Search Results:
- Project documents found: {project_count}
- Code examples found: {code_count}
- Training manual sections found: {coop_count}
- Projects: {projects_list}
- Search scope: {search_scope}

Provide a comprehensive technical summary of the retrieval results, including all project numbers, document types, and relevance explanations."""),
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
            ("system", """You are providing a detailed technical assessment to a structural engineer of the document relevance filtering process.

Your job is to provide a COMPREHENSIVE FILTERING ANALYSIS including:
1. Detailed explanation of the review criteria used to assess document relevance
2. Specific technical requirements that documents must meet (e.g., must contain load calculations, not just mentions of beams)
3. Complete breakdown of filtering results with counts and percentages
4. Specific examples of why documents were kept (what relevant information they contain)
5. Specific examples of why documents were filtered out (what they were missing or why they were insufficient)
6. Types of information verified (design calculations, material specifications, code references, construction details)
7. Quality assessment of the remaining documents (completeness, detail level, applicability)

FORMATTING AND STYLE REQUIREMENTS:
- Use professional section header: "RELEVANCE ASSESSMENT"
- Write in detailed, technical paragraphs (5-7 sentences minimum)
- Provide specific percentages: "Retained 75 of 100 documents (75% pass rate)"
- Give concrete examples: "Kept documents that included specific beam sizes (W16x31), load calculations (DL + LL), and connection details"
- Explain filtering criteria: "Filtered out documents that only mentioned beams in passing without sizing information, load data, or material specifications"
- Reference document quality indicators: "complete design calculations", "detailed specifications", "code-compliant details"
- Include information about what makes retained documents valuable
- NO emojis or casual language
- NO mentions of scoring algorithms or technical implementation

EXAMPLE OF GOOD TECHNICAL FILTERING ANALYSIS:
"RELEVANCE ASSESSMENT

The document review process evaluated all 100 retrieved documents against specific technical criteria to ensure they contained substantive structural design information relevant to steel beam design. Review criteria included: presence of beam sizing calculations, material specifications (ASTM grade), load analysis documentation, connection design details, and code reference citations (AISC 360, IBC). Documents were required to demonstrate complete design information rather than merely mentioning steel beams in peripheral contexts.

Of the 100 documents reviewed, 100 documents (100%) met the relevance criteria and were retained for detailed analysis. All retained documents contain specific design details including beam member sizes (W-sections with depth and weight designations), load calculations showing dead load and live load components, material specifications referencing ASTM A992 steel, and connection methods with bolt or weld specifications. No documents were filtered out as all retrieved materials demonstrated substantive engineering content directly applicable to the query requirements.

The high retention rate indicates strong initial search effectiveness, with retrieved documents showing consistent quality in terms of calculation completeness, specification detail, and design documentation standards. Retained documents represent a comprehensive reference set spanning multiple design approaches and project types, providing diverse examples of code-compliant steel beam design methodologies."

AVOID:
- Generic statements like "documents were reviewed for relevance"
- Missing specific counts and percentages
- No explanation of what makes documents relevant or irrelevant
- Vague criteria without technical specifics"""),
            ("user", """Engineer's Question: "{query}"

Filtering Results:
- Total documents reviewed: {retrieved_count}
- Documents meeting relevance criteria: {graded_count}
- Documents filtered out: {filtered_out}

Provide a comprehensive technical assessment of the document filtering process, including specific criteria, examples, and quality evaluation."""),
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
            ("system", """You are providing a detailed technical compilation summary to a structural engineer explaining how their answer is being assembled.

Your job is to provide a COMPREHENSIVE COMPILATION REPORT including:
1. Complete list of all projects being analyzed with specific project numbers
2. Types of information being extracted from each source (calculations, drawings, specifications, details)
3. Specific technical elements being compiled (beam sizes, load values, material specs, connection types)
4. Organization strategy: how information is being structured (by project, by design approach, chronologically, by load capacity, etc.)
5. Cross-references between projects showing common approaches or variations
6. Additional reference sources being included (code examples with section numbers, training materials with page numbers)
7. Quality and completeness assessment of the compiled information
8. Expected deliverables in the final answer (tables, calculations, design examples, specification excerpts)

FORMATTING AND STYLE REQUIREMENTS:
- Use professional section header: "INFORMATION COMPILATION"
- Write in detailed, technical paragraphs (6-8 sentences minimum)
- List ALL project numbers being used
- Specify exact information types: "extracting W-section beam schedules, shear and moment diagrams, connection details from shop drawings"
- Describe organization method: "organizing by span length categories (10-20ft, 20-30ft, 30-40ft) to facilitate comparison"
- Reference specific code sections: "including AISC 360 Chapter F provisions for flexural design"
- Explain value of each information source
- Describe how information will be presented (comparison tables, design example walkthroughs, specification templates)
- NO emojis or casual language
- NO mentions of synthesis algorithms or generation processes

EXAMPLE OF GOOD TECHNICAL COMPILATION REPORT:
"INFORMATION COMPILATION

Compiling comprehensive steel beam design information from 12 structural engineering projects: 25-01-006, 25-01-017, 25-01-022, 25-01-038, 25-01-045, 25-01-052, 25-01-063, 25-01-071, 25-01-084, 25-01-091, 25-01-098, and 25-01-105. From these projects, extracting complete design information including beam member sizes (W-sections with depth and weight designations), load calculations showing dead load, live load, and load combinations per ASCE 7, material specifications (ASTM A992 Grade 50 steel properties), deflection limits (L/360 for live load, L/240 for total load), and connection details (bolted and welded configurations with specific bolt sizes and weld dimensions).

Information is being organized by beam span ranges to facilitate direct comparison of design approaches: short spans (10-20 feet), medium spans (20-35 feet), and long spans (35-50 feet). For each span category, presenting example calculations demonstrating load analysis, section selection using AISC Manual tables, deflection verification, and connection capacity checks. Additionally incorporating 50 code reference examples providing AISC 360 design procedures (Chapter F for flexural members, Chapter J for connections), load combination methodologies from ASCE 7, and material property tables from AISC Manual Part 1.

The compiled information represents complete design documentation spanning initial loading assumptions through final member selection and detailing, providing both theoretical design procedures and practical implementation examples from successfully completed projects. Final answer will present information in structured format including design procedure step-by-step guides, comparison tables showing member selections across projects, calculation examples with detailed commentary, and specification templates for material and fabrication requirements."

AVOID:
- Generic statements like "organizing information"
- Missing project numbers or vague project references
- No description of organization method
- Lack of specific technical content details"""),
            ("user", """Engineer's Question: "{query}"

Information Sources:
- Technical documents: {graded_count}
- Projects referenced: {projects_list}
- Code examples included: {has_code}
- Standards/training materials included: {has_coop}

Provide a comprehensive technical compilation report detailing all projects, information types, organization strategy, and expected deliverables."""),
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

