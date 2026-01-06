"""
Router Selection Prompts - For selecting which routers to use
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_fast

ROUTER_SELECTION_PROMPT = PromptTemplate.from_template(
    """You are a routing assistant that determines which router(s) should handle a user's query.

AVAILABLE ROUTERS:
1. "rag": Use for queries requiring database/document search in Supabase
   - BIM data search
   - Engineering drawings search
   - Project documents search
   - Specifications and technical documentation
   - Document retrieval and information extraction
   - Example queries: "Find projects with floating slabs", "Search for retaining wall designs", "Show me barndominium projects"

2. "web": Use for queries requiring web applications or Python tools
   - Calculators (general purpose, engineering calculators)
   - SkiCiv API (structural analysis and design tools)
   - Jabacus API (engineering calculations and analysis)
   - OpenSeaspy (Python library for structural engineering analysis)
   - Other web-based engineering tools and APIs
   - Example queries: "Calculate beam deflection", "Use SkiCiv to analyze this structure", "Run a calculation using Jabacus"

3. "desktop": Use for queries requiring desktop applications
   - Excel operations (spreadsheets, data analysis, file manipulation)
   - Word operations (document processing, text editing)
   - File operations on user's desktop (reading/writing files, file system access)
   - Example queries: "Open the Excel file on my desktop", "Read data from a spreadsheet", "Create a Word document"

DECISION PROCESS:
1. Does the query require searching databases, documents, or retrieving information from stored data?
   → YES: Include "rag"
   → NO: Continue to step 2

2. Does the query require calculations, computations, or web-based tools/APIs?
   → YES: Include "web"
   → NO: Continue to step 3

3. Does the query require desktop applications (Excel, Word) or file operations?
   → YES: Include "desktop"
   → NO: Continue to step 4

4. If none of the above apply, default to "rag" for information retrieval

IMPORTANT:
- You can select MULTIPLE routers if the query requires multiple types of resources
- Select ALL routers that are relevant to answering the query
- Be thorough in your analysis

CRITICAL: Return ONLY valid JSON, no explanations or preamble. Start your response with {{ and end with }}.

JSON Format:
{{
  "routers": ["rag"],
  "reasoning": "Brief explanation of why these routers were selected"
}}

Question: {q}
Response:"""
)

# Use fast LLM for router selection
router_selection_llm = llm_fast

