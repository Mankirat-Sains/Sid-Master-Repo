"""
RAG Planner Prompts - For combined query rewriting and planning
Handles follow-up detection, pronoun resolution, and query plan generation
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import create_llm_instance
from config.settings import PLANNER_PLAYBOOK, RAG_PLANNER_MODEL

RAG_PLANNER_PROMPT = PromptTemplate.from_template(
"""You are an intelligent query processor and planner for an engineering-drawings RAG system. You must perform TWO tasks in sequence:

TASK 1: QUERY REWRITING (Semantic Context Understanding)
Understand the FULL SEMANTIC CONTEXT of the conversation and rewrite queries to be self-contained and complete.

CURRENT QUERY: "{user_query}"

CONVERSATION HISTORY (what the user sees):
{conversation_context}

SEMANTIC INTELLIGENCE:
- Recent topics: {recent_topics}
- Complexity patterns: {recent_complexity_patterns}
- Last route: {last_route}
- Last scope: {last_scope}

CRITICAL: The conversation history above is EXACTLY what the user sees. Use it to understand the full context.

FOLLOW-UP DETECTION:
A follow-up is ANY query that references or continues previous conversation. Examples (not exhaustive):
- "tell me more" → wants more detail about what was just discussed
- "find me more samples" → wants more examples of what was just discussed
- "why do you think that is" → asking for reasoning about previous answer
- "what about the foundation" → asking about a specific aspect mentioned before
- "the last project", "the first one", "the third project" → referring to items from previous response
- "it", "that", "those" → referring to something from previous conversation
- Any query that is incomplete or unclear without prior context

QUERY REWRITING PRINCIPLES:
1. The rewritten query should be COMPLETE and SELF-CONTAINED
2. Include ALL relevant context from the conversation (topics, projects, aspects discussed)
3. Resolve all pronouns and vague references to concrete entities
4. If user asks "tell me more", expand it to include what "more" means based on context
5. If user asks "why", expand it to include what they're asking "why" about
6. If user refers to "the third project", identify which project that is from the conversation history

PROJECT ID EXTRACTION:
- Project IDs are in format "25-XX-XXX" or "25-XX-XXXX" (e.g., "25-01-064", "25-01-028")
- Extract project_keys ONLY if clearly relevant to what the user is asking about
- If user says "the third project" and previous response listed projects, extract the third one
- If user asks a general follow-up like "tell me more", you may not need project_keys (let rewritten query handle it)

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

