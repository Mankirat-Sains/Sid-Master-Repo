"""
Enhanced Planning Prompts - Deep Agents Capabilities
Includes complexity detection, task decomposition, and execution planning
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_fast
from config.settings import PLANNER_PLAYBOOK

# Limit playbook size to avoid token limits
MAX_PLAYBOOK_LENGTH = 2000


COMPLEXITY_DETECTION_PROMPT = PromptTemplate.from_template(
    """You are a query complexity analyzer. Determine if a user query requires task decomposition and multi-step planning.

A query is COMPLEX if it:
- Requires multiple distinct actions or steps
- Needs information from one step to proceed to the next
- Involves multiple routers working in sequence
- Contains words like: "design and verify", "calculate then check", "find and analyze", "create and generate"
- Requires coordination between different systems (search → calculate → document)

A query is SIMPLE if it:
- Can be answered with a single action
- Requires only one router
- Is a straightforward information request
- Contains single verbs: "find", "search", "calculate", "show"

CRITICAL: Return ONLY valid JSON, no explanations. Start with {{ and end with }}.

JSON Format:
{{
  "is_complex": true/false,
  "reasoning": "Brief explanation"
}}

Question: {q}
Response:"""
)


EXECUTION_PLANNING_PROMPT = PromptTemplate.from_template(
    """You are an engineering task planner. Break down complex engineering queries into executable steps with router assignments.

AVAILABLE ROUTERS AND THEIR CAPABILITIES:

1. "rag" - Information Retrieval & Database Search
   - Search databases, documents, BIM data in Supabase
   - Find engineering drawings, specifications, project documents
   - Retrieve building codes, standards, technical documentation
   - Extract information from stored data
   - Example tasks: "Find projects with floating slabs", "Search for beam designs", "Retrieve code requirements"

2. "web" - Calculations & Analysis Tools
   - Structural calculations (loads, deflections, stresses, capacities)
   - SkyCiv API for structural analysis and design
   - Jabacus API for engineering calculations
   - Python-based analysis tools (OpenSeaspy, etc.)
   - General purpose calculators
   - Example tasks: "Calculate beam deflection", "Analyze structure with SkyCiv", "Run load calculations"

3. "desktop" - File Operations & Desktop Applications
   - Excel operations (read/write spreadsheets, data analysis)
   - Word document creation/editing
   - File system access (reading/writing files)
   - Example tasks: "Create calculation report in Excel", "Generate Word document", "Read data from spreadsheet"

ENGINEERING WORKFLOW KNOWLEDGE:
{playbook}

PLANNING PRINCIPLES:

1. **Task Dependencies**: Some tasks must happen in sequence
   - Example: "Design a beam and verify it meets code"
     - Step 1: Retrieve design requirements (rag) → needs input data
     - Step 2: Calculate required beam capacity (web) → uses loads from Step 1
     - Step 3: Design beam section (web) → uses capacity from Step 2
     - Step 4: Verify code compliance (rag) → checks design from Step 3
     - Step 5: Generate design report (desktop) → documents all results

2. **Parallel Execution**: Independent tasks can run simultaneously
   - Example: "Find beam designs and calculate deflection"
     - Step 1: Search for beam designs (rag) → can run in parallel
     - Step 2: Calculate deflection (web) → can run in parallel

3. **Information Flow**: Later steps often need results from earlier steps
   - Always check if a step needs output from a previous step
   - Mark dependencies explicitly in the plan

4. **Completion Criteria**: Each step should have clear success criteria
   - "Calculate loads" → complete when load values are obtained
   - "Verify code" → complete when code check passes/fails
   - "Generate report" → complete when document is created

TASK BREAKDOWN RULES:
- Break complex queries into 2-8 steps (typically 3-5 steps)
- Each step should be a single, focused action
- Steps should be ordered by dependencies (no step depends on a later step)
- Mark which router handles each step
- Include status tracking (pending/in-progress/complete)
- Note what information flows between steps
- Include expected outputs for each step

EXECUTION PLAN STRUCTURE:
Each step in the execution plan should include:
- step: Sequential step number (1, 2, 3...)
- description: Clear, actionable description of what this step does
- router: Which router handles this step ("rag", "web", or "desktop")
- status: Initial status is always "pending"
- dependencies: List of step numbers this step depends on (empty list if none)
- expected_output: What information or result this step produces

CRITICAL: Return ONLY valid JSON, no explanations or preamble. Start your response with {{ and end with }}.

JSON Format:
{{
  "is_complex": true,
  "selected_routers": ["rag", "web"],
  "execution_plan": [
    {{
      "step": 1,
      "description": "Clear step description",
      "router": "rag",
      "status": "pending",
      "dependencies": [],
      "expected_output": "What this step produces"
    }},
    {{
      "step": 2,
      "description": "Next step",
      "router": "web",
      "status": "pending",
      "dependencies": [1],
      "expected_output": "What this step produces"
    }}
  ],
  "reasoning": "Why this plan was created and how steps relate"
}}

Question: {q}
Response:"""
)


# Use fast LLM for planning
planning_llm = llm_fast
