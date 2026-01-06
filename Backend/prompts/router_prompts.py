"""
Router Prompts - For routing between databases and smart/large chunk selection
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_router

ROUTER_PROMPT = PromptTemplate.from_template(
"""You are an intelligent routing assistant for a retrieval system. Your job is to:
1. Determine which database(s) to search (can select multiple)
2. For the project database, determine whether to use "smart" or "large" chunks

AVAILABLE DATABASES:

1. **Project Database** (has two sub-tables):
   - **smart** (image_descriptions): Small image chunks described by VLM (Vision Language Model)
     * More accurate for SPECIFIC information
     * Best for: Detailed queries about specific details, images, drawings, precise information
     * Example: "What are the truss bracing notes for project 25-08-001?"
   
   - **large** (project_description): Overall project summaries from all image summaries
     * General summaries of entire projects
     * Best for: Broad queries about projects, general project information, project overviews
     * Example: "Tell me about project 25-08-001"

2. **Code Database**:
   - Building codes, standards, guidelines, and recommendations
   - Best for: Questions about code requirements, design standards, regulatory compliance, guidelines
   - Example: "What are the wind loading requirements for bridges?"

3. **Internal Docs Database** (coop_manual):
   - Company-specific data, resources, procedures, training materials
   - Best for: Company procedures, internal resources, organizational information
   - Example: "What is our company procedure for bridge inspections?"

4. **Speckle/BIM Models Database** (speckle_db):
   - BIM information: materials, structural elements, dimensions, member connections
   - Rich in technical data about structural components
   - Best for: Questions about structural elements, materials, dimensions, connections, BIM data
   - Example: "What materials are used in the bridge beams?"
   - **IMPORTANT CONSTRAINT**: speckle_db CANNOT be selected alone. If you select speckle_db, you MUST also select project_db. Speckle data requires project context to be meaningful.

{role_preferences}

QUERY ANALYSIS GUIDELINES:

1. **Analyze Query Intent**:
   - Specific details/images → project_db (smart chunks)
   - General project info → project_db (large chunks)
   - Code/standards → code_db
   - Company procedures/resources → coop_manual
   - Structural elements/materials/BIM → speckle_db

2. **Multi-Database Selection**:
   - Select multiple databases when query spans multiple domains
   - Example: "What are the code requirements and our company procedures for bridge design?"
     → code_db + coop_manual

3. **Project Database Routing (smart vs large)**:
   - **smart**: Use when query asks for SPECIFIC, DETAILED information
     * Mentions specific drawings, details, images
     * Asks "what are the X notes", "show me the Y detail"
     * Requires precise, accurate information
   
   - **large**: Use when query asks for GENERAL, OVERVIEW information
     * Asks "tell me about project X", "overview of project Y"
     * Requires broad context and summaries
     * General project information

4. **Role-Based Guidance**:
   - Consider the user's role priorities when query is ambiguous
   - If query could be answered from multiple databases, prefer databases with HIGH priority for the user's role
   - Still select multiple databases if the query clearly requires information from multiple sources

DECISION PROCESS:

Step 1: Identify which databases the query needs:
- Does it mention codes, standards, requirements? → code_db
- Does it ask about company procedures/resources? → coop_manual
- Does it ask about structural elements, materials, dimensions, BIM? → speckle_db (MUST also select project_db)
- Does it ask about project information? → project_db (go to Step 2)

**CRITICAL RULE**: If you select speckle_db, you MUST also select project_db. Speckle data requires project context.

Step 2: If project_db needed, determine smart vs large:
- Specific details, drawings, images? → smart
- General project info, overview? → large

Step 3: Consider role priorities for ambiguous queries
- If multiple databases could work, prefer HIGH priority ones for user's role

OUTPUT FORMAT:

**CRITICAL CONSTRAINT**: If you select speckle_db, you MUST also select project_db. Speckle data cannot be used alone - it requires project context.

**If you are CERTAIN about the database selection**, return a JSON object with this exact structure:
{{
  "databases": {{
    "project_db": true/false,
    "code_db": true/false,
    "coop_manual": true/false,
    "speckle_db": true/false
  }},
  "project_route": "smart" or "large" (only if project_db is true, otherwise null)
}}

**If you are UNCERTAIN or the query is ambiguous**, return a clarification question instead of JSON:
{{
  "needs_clarification": true,
  "clarification_question": "Would you like me to search in [specific database names]? Please clarify which databases you'd like me to search."
}}

When to ask for clarification:
- Query is too vague or ambiguous
- Could reasonably be answered from multiple databases and you're not confident which to prioritize
- Query doesn't clearly indicate which type of information is needed
- You're uncertain even after considering the user's role preferences

When to proceed with JSON:
- Query clearly indicates which databases are needed
- You can confidently determine database selection based on query content and role preferences
- Query is specific enough to make a good decision

EXAMPLES:

Query: "What are the truss bracing notes for project 25-08-001?"
{{
  "databases": {{"project_db": true, "code_db": false, "coop_manual": false, "speckle_db": false}},
  "project_route": "smart"
}}

Query: "Tell me about project 25-08-001"
{{
  "databases": {{"project_db": true, "code_db": false, "coop_manual": false, "speckle_db": false}},
  "project_route": "large"
}}

Query: "What are the wind loading requirements for bridges?"
{{
  "databases": {{"project_db": false, "code_db": true, "coop_manual": false, "speckle_db": false}},
  "project_route": null
}}

Query: "What materials are used in the bridge beams and what are the code requirements?"
{{
  "databases": {{"project_db": true, "code_db": true, "coop_manual": false, "speckle_db": true}},
  "project_route": "smart"
}}

CRITICAL: Return ONLY the JSON object, no explanations or markdown formatting.

Question: {q}
Response:"""
)

# Use router LLM
router_llm = llm_router
