"""
Planner Prompts - For query planning and decomposition
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_fast
from config.settings import PLANNER_PLAYBOOK

PLANNER_PROMPT = PromptTemplate.from_template(
"""You produce an executable query plan (a sequence of ops) for a RAG system over engineering drawings.

You have these GENERIC OPS (compose them as needed):
- RETRIEVE(queries, k)                             # query vector+keyword hybrid retriever (automatically includes MMR diversification for relevance)
- EXTRACT(target)                                   # synthesis focuses on 'target' using ALL retrieved content
- LIMIT_PROJECTS(n)                                 # after synthesis, keep docs from the first n distinct projects

Guidelines:
- Break the user question into steps using these ops.
- Use domain synonyms in queries/tokens (provide them explicitly).
- If the user mentions a specific month (e.g., "in March", "March projects"), note it but don't add metadata filters unless the table supports them.
- If the user asks for a specific number of projects, include LIMIT_PROJECTS(N).
- If the user asks for comprehensive coverage, counting, or "all" projects, use LIMIT_PROJECTS("infer") which will intelligently determine the appropriate limit.
- For general queries without specific requirements, use LIMIT_PROJECTS("infer") with default of 20.
- Use EXTRACT first to synthesize ALL retrieved content before limiting projects
- Use LIMIT_PROJECTS after synthesis to select the most relevant projects
- IMPORTANT: Recency sorting is handled automatically by the LLM during synthesis - documents are already ranked by relevance (via MMR), and the LLM will organize the response by recency when listing projects. Do NOT add RANK_BY_RECENCY operation.

CONVERSATION CONTEXT (if provided):
- Use conversation history below ONLY to resolve ambiguous references like "the second one", "that project", "it", etc.
- PRIORITIZE THE MOST RECENT EXCHANGE - unless the user explicitly mentions "originally", "the first question", "earlier", assume they mean the most recent exchange.
- DO NOT restrict retrieval based on prior projects - always search the full database unless the question explicitly asks about a specific prior project.
- Example 1: "Tell me about the 2nd project" → Look up which project that is from the MOST RECENT answer, then search specifically for it.
- Example 2: "Find me more projects with the same size as the 2nd project" → Look up the 2nd project's dimensions from the MOST RECENT answer, then search ALL projects for that size.
- Expand queries with concrete details (dimensions, features) extracted from the MOST RECENT conversation context, not just project IDs.

{conversation_context}

CRITICAL: Return ONLY valid JSON, no explanations or preamble. Start your response with {{ and end with }}.

JSON Format:
{{
  "reasoning": "...",
  "steps": [
    {{"op":"RETRIEVE","args":{{"queries":["...","..."]}}}},
    {{"op":"EXTRACT","args":{{"target":"..."}}}},
    {{"op":"LIMIT_PROJECTS","args":{{"n":"infer"}}}}
  ]
}}

PLAYBOOK:
{playbook}

CURRENT QUESTION:
{q}

Remember: Return ONLY the JSON object, nothing else.

Key Notes:
- Ensure your reasoning is very thorough and detailed. They should clearly describe how you are decomposing the user query and how that is influencing what you, the best structural engineering agent in the world, are searching for.
"""
)

# Create planner LLM with JSON output format
planner_llm = llm_fast

