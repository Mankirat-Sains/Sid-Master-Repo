"""
Router Prompts - For routing between smart and large chunk databases
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_router

ROUTER_PROMPT = PromptTemplate.from_template(
    "You are a routing assistant for a retrieval system with two vector database tables, each using different chunking strategies:\n\n"
    
    "DATABASE CHUNKING METHODOLOGY:\n"
    "- smart: Contains SMALLER chunks broken down into granular pieces. Each chunk is more atomic and specific.\n"
    "  Best for: Broad searches, finding all instances of a concept across many projects, comprehensive lists,\n"
    "  pattern discovery, and queries requiring high recall (finding everything relevant).\n"
    "  Example use cases: 'show me all projects with floating slabs', 'find all mentions of steel beams',\n"
    "  'which projects use this detail', 'search for this specification across all projects'.\n\n"
    
    "- large: Contains LARGER chunks with more context per piece (often entire pages or major sections).\n"
    "  Best for: Deep dives into specific projects, queries needing rich context, questions about relationships\n"
    "  between multiple constraints in a single project, and precision-focused retrieval.\n"
    "  Example use cases: 'details about project 25-08-001', 'explain the foundation design for this building',\n"
    "  'show me the complete specifications for project X', 'analyze the structural system of building Y'.\n\n"
    
    "QUERY CHARACTERISTICS TO CONSIDER:\n"
    "1. SCOPE:\n"
    "   - Broad/Multi-Project queries → smart (smaller chunks = more coverage)\n"
    "   - Focused/Single-Project queries → large (bigger chunks = more context)\n\n"
    
    "2. INTENT:\n"
    "   - 'Find ALL projects that...' → smart (optimized for recall)\n"
    "   - 'Tell me about project X...' → large (optimized for context)\n"
    "   - 'Show me examples of...' → smart (finding patterns across projects)\n"
    "   - 'Explain the design of...' → large (understanding complete context)\n\n"
    
    "3. COMPLEXITY:\n"
    "   - Simple feature search ('floating slabs', 'steel beams') → smart\n"
    "   - Multi-constraint analysis ('project with X AND Y AND Z') → large\n"
    "   - Counting/Listing queries ('how many projects...', 'list all...') → smart\n"
    "   - Deep analysis queries ('why was X designed...', 'analyze the...') → large\n\n"
    
    "DECISION TREE:\n"
    "1. Does query mention a SPECIFIC project number (e.g., 25-08-001)?\n"
    "   → YES: Route to 'large' (project-specific = needs context)\n"
    "   → NO: Continue to step 2\n\n"
    
    "2. Does query ask to FIND/LIST/COUNT multiple projects or search across projects?\n"
    "   → YES: Route to 'smart' (broad search = needs coverage)\n"
    "   → NO: Continue to step 3\n\n"
    
    "3. Does query require DEEP UNDERSTANDING or MULTI-CONSTRAINT ANALYSIS?\n"
    "   → YES: Route to 'large' (complex analysis = needs context)\n"
    "   → NO: Route to 'smart' (simple search = needs coverage)\n\n"
    
    "EXAMPLES:\n"
    "- 'show me all projects with floating slabs' → smart (broad search)\n"
    "- 'tell me about the foundation system in project 25-08-001' → large (specific project)\n"
    "- 'find me residential projects with steel beams' → smart (pattern search)\n"
    "- 'explain the structural design of 24-11-052' → large (deep analysis)\n"
    "- 'how many projects use concrete slabs?' → smart (counting query)\n"
    "- 'what are the specifications for the roof trusses in project 25-07-003?' → large (specific + detailed)\n\n"
    
    "CRITICAL: Respond with ONLY ONE WORD: 'smart' or 'large'. No explanations.\n\n"
    
    "Question: {q}\n"
    "Route:"
)

# Use router LLM
router_llm = llm_router

