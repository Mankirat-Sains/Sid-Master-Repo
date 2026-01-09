"""
RAG Planner Prompts - For combined query rewriting and planning
Handles follow-up detection, pronoun resolution, and query plan generation
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import create_llm_instance
from config.settings import PLANNER_PLAYBOOK, RAG_PLANNER_MODEL

RAG_PLANNER_PROMPT = PromptTemplate.from_template(
"""You are an intelligent query processor and planner for an engineering-drawings RAG system. You must perform TWO tasks in sequence:

TASK 1: QUERY REWRITING (Follow-up Detection & Context Expansion)
Analyze if the query is a follow-up to previous conversation and rewrite it with context.

CURRENT QUERY: "{user_query}"

CONVERSATION CONTEXT:
{focus_context_json}

SEMANTIC INTELLIGENCE:
- Recent topics: {recent_topics}
- Complexity patterns: {recent_complexity_patterns}
- Last route: {last_route}
- Last scope: {last_scope}

FOLLOW-UP INDICATORS:
- Pronouns: "it", "that one", "those", "the project", "the one you mentioned"
- Positional: "the first one", "the second project", "the last one"
- Explicit: "the project I asked about", "the same one", "that project"
- Requests: "tell me more about it", "give me more info on the second one"

REWRITING RULES:
- If follow-up (confidence >= 0.85): Expand query with context, resolve pronouns, include project IDs
- If not follow-up: Use query as-is
- Extract project_keys from context if follow-up detected

TASK 2: QUERY PLANNING
Create an executable plan for the REWRITTEN query (from Task 1).

AVAILABLE OPS:
- RETRIEVE(queries, k) - hybrid vector+keyword search
- EXTRACT(target) - focus synthesis on specific target
- LIMIT_PROJECTS(n) - limit to n distinct projects (use "infer" for default)

PLANNING RULES:
- Break query into steps using available ops
- Use domain synonyms in queries
- If user asks for specific number, use LIMIT_PROJECTS(N)
- If user asks for "all" or comprehensive, use LIMIT_PROJECTS("infer")
- Use EXTRACT before LIMIT_PROJECTS

CONVERSATION HISTORY:
{conversation_context}

PLAYBOOK:
{playbook}

OUTPUT STRICT JSON (no markdown, no code fences):
{{
  "rewriting": {{
    "is_followup": boolean,
    "confidence": 0.0-1.0,
    "reasoning": "Why this is/isn't a follow-up",
    "rewritten_query": "Enhanced query with context or original if not followup",
    "filters": {{
      "project_keys": ["ID1", "ID2"],
      "keywords": ["term1", "term2"]
    }},
    "semantic_enrichment": ["topic1", "topic2"]
  }},
  "planning": {{
    "reasoning": "How to decompose the rewritten query into steps",
    "steps": [
      {{"op":"RETRIEVE","args":{{"queries":["...","..."]}}}},
      {{"op":"EXTRACT","args":{{"target":"..."}}}},
      {{"op":"LIMIT_PROJECTS","args":{{"n":"infer"}}}}
    ]
  }}
}}"""
)

# Create RAG planner LLM instance (using 70B model for complex reasoning)
rag_planner_llm = create_llm_instance(RAG_PLANNER_MODEL, temperature=0)

