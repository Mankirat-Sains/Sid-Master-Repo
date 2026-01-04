"""
Session Memory & Focus State Management
Handles conversation history, follow-up detection, and query rewriting
"""
import re
import json
from typing import Dict, TypedDict, Optional, Tuple, List

# Import configurations and LLM instances
from config.logging_config import log_query
from config.llm_instances import llm_fast
from config.settings import MAX_CONVERSATION_HISTORY, MAX_SEMANTIC_HISTORY


# =============================================================================
# MEMORY LIMITS
# =============================================================================

# Maximum number of conversation exchanges to keep in memory
MAX_CONVERSATION_HISTORY = 10

# Maximum number of semantic intelligence records to keep
MAX_SEMANTIC_HISTORY = 5
# =============================================================================
# MEMORY STORAGE
# =============================================================================

# Session memory - stores conversation history and semantic intelligence
SESSION_MEMORY: Dict[str, Dict] = {}

# Focus state - tracks recent projects and queries for intelligent rewriting
FocusState = TypedDict("FocusState", {
    "recent_projects": List[str],        # MRU, dedup, max ~10
    "last_answer_projects": List[str],   # extracted from last answer
    "last_results_projects": List[str],  # extracted from last retrieval
    "last_query_text": str,
})

FOCUS_STATES: Dict[str, FocusState] = {}


# =============================================================================
# FOCUS STATE MANAGEMENT
# =============================================================================

def update_focus_state(
    session_id: str,
    query: str,
    projects: List[str] = None,
    results_projects: List[str] = None
):
    """
    Update focus state with new information from the current interaction.
    
    Args:
        session_id: Unique session identifier
        query: Current query text
        projects: Projects mentioned in the answer
        results_projects: Projects from retrieval results
    """
    if session_id not in FOCUS_STATES:
        FOCUS_STATES[session_id] = {
            "recent_projects": [],
            "last_answer_projects": [],
            "last_results_projects": [],
            "last_query_text": ""
        }
    
    state = FOCUS_STATES[session_id]
    
    # Update recent projects (MRU, dedup, max 10)
    if projects:
        for p in projects:
            if p in state["recent_projects"]:
                state["recent_projects"].remove(p)
            state["recent_projects"].append(p)
        state["recent_projects"] = state["recent_projects"][-10:]  # Keep last 10
    
    if results_projects:
        state["last_results_projects"] = results_projects
    
    state["last_query_text"] = query
    
    log_query.info(
        f"🎯 FOCUS STATE UPDATED: recent_projects={state['recent_projects'][-3:]}, "
        f"last_results={state['last_results_projects'][:3]}"
    )


# =============================================================================
# SEMANTIC CONTEXT EXTRACTION
# =============================================================================

def _extract_semantic_context_for_rewriter(session_data: dict) -> dict:
    """
    Extract semantic context for query rewriting from session memory.
    Analyzes planning, routing, and execution patterns from previous interactions.
    """
    last_semantic = session_data.get("last_semantic", {})
    semantic_history = session_data.get("semantic_history", [])
    
    # Extract recent topics and complexity patterns
    recent_topics = []
    recent_complexity = []
    recent_operations = []
    
    # Get data from last semantic intelligence
    if last_semantic:
        planning = last_semantic.get("planning", {})
        routing = last_semantic.get("routing", {})
        execution = last_semantic.get("execution", {})
        
        recent_topics.extend(planning.get("topics_explored", []))
        recent_complexity.append(planning.get("complexity_assessment", ""))
        recent_operations.extend(execution.get("operations_performed", []))
    
    # Get patterns from semantic history (last 2-3 exchanges)
    for semantic_record in semantic_history[-2:]:
        planning = semantic_record.get("planning", {})
        recent_topics.extend(planning.get("topics_explored", []))
        recent_complexity.append(planning.get("complexity_assessment", ""))
    
    return {
        "recent_topics": list(set([t for t in recent_topics if t]))[:5],  # Unique, limit to 5
        "recent_complexity_patterns": list(set([c for c in recent_complexity if c]))[:3],
        "recent_operation_patterns": list(set([o for o in recent_operations if o]))[:5],
        "last_route": last_semantic.get("routing", {}).get("data_route", ""),
        "last_scope": last_semantic.get("routing", {}).get("scope_assessment", "")
    }


# =============================================================================
# INTELLIGENT QUERY REWRITING
# =============================================================================

def intelligent_query_rewriter(user_query: str, session_id: str) -> Tuple[str, dict]:
    """
    Use LLM to intelligently rewrite queries and detect follow-ups.
    Handles pronoun resolution, follow-up detection, and context expansion.
    
    Args:
        user_query: The user's raw query
        session_id: Session identifier for context retrieval
    
    Returns:
        Tuple of (rewritten_query, filters_dict)
    """
    # Guardrail 1: Extract explicit project IDs with regex
    explicit_ids = re.findall(r'\b\d{2}-\d{2}-\d{3}\b', user_query)
    if explicit_ids:
        log_query.info(f"🎯 EXPLICIT IDs DETECTED: {explicit_ids}")
        return user_query, {"project_keys": explicit_ids}
    
    # Get focus state
    focus_state = FOCUS_STATES.get(session_id, {
        "recent_projects": [],
        "last_answer_projects": [],
        "last_results_projects": [],
        "last_query_text": ""
    })
    
    # SEMANTIC INTELLIGENCE: Get semantic context from session memory
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_context = _extract_semantic_context_for_rewriter(session_data)
    
    # Enhanced LLM-based rewriting with semantic intelligence
    focus_context = {
        "recent_projects": focus_state["recent_projects"][-5:],  # Last 5 recent
        "last_answer_projects": focus_state["last_answer_projects"],
        "last_results_projects": focus_state["last_results_projects"],
        "last_query": focus_state["last_query_text"],
        # NEW: Semantic intelligence
        "recent_topics": semantic_context["recent_topics"],
        "recent_complexity": semantic_context["recent_complexity_patterns"],
        "last_route_preference": semantic_context["last_route"],
        "last_scope_pattern": semantic_context["last_scope"]
    }
    
    log_query.info(f"🎯 FOCUS CONTEXT FOR REWRITER: {focus_context}")
    
    prompt = f"""You are a classifier for an engineering-drawings RAG system. Your job is to determine if a query is a follow-up to previous conversation.

CURRENT QUERY: "{user_query}"

CONVERSATION CONTEXT:
{json.dumps(focus_context, indent=2)}

SEMANTIC INTELLIGENCE:
- Recent topics explored: {semantic_context["recent_topics"]}
- Recent complexity patterns: {semantic_context["recent_complexity_patterns"]}  
- Last route preference: {semantic_context["last_route"]}
- Last scope pattern: {semantic_context["last_scope"]}

TASK: Analyze if this query is a follow-up to previous conversation context.

FOLLOW-UP INDICATORS (clear signals that indicate follow-up):
- Explicit references to prior context:
  * Pronouns: "it", "that one", "those", "the project", "the one you mentioned"
  * Positional references: "the first one", "the second project", "the last one", "the second one"
  * Explicit references: "the project I asked about", "the same one", "that project"
  * Requests for more info: "tell me more about it", "give me more info on the second one"
- Query is incomplete without prior context (unclear what "it", "that", "the second one" refers to)
- Query continues previous topic: "also", "additionally", "furthermore" (when clearly continuing same topic)
- Query asks for different perspective on same topic from prior conversation

NON-FOLLOW-UP INDICATORS (clear signals that indicate NEW query):
- Complete, self-contained questions that make sense without context
- New topics unrelated to recent conversation
- Explicit project IDs mentioned (25-XX-XXX format) - these are explicit, not follow-ups
- Specific dates/locations that weren't discussed recently
- Questions that clearly introduce new information or shift focus to unrelated topic
- General questions about engineering concepts (not referencing prior results)
- Questions that could be answered independently without prior context

CLASSIFICATION RULES:
- If query contains pronouns/positional references ("it", "the second one", "that project"), it's likely a follow-up
- If query is self-contained and makes sense without context, it's likely NOT a follow-up
- BE CONSERVATIVE: When genuinely ambiguous, classify as "new" (not follow-up)
- Only classify as follow-up if you can identify what prior context is being referenced

CONFIDENCE GUIDELINES:
- 0.95-1.0: Strong evidence (pronouns, "the second one", "tell me more about it", etc.)
- 0.85-0.94: Clear evidence but some ambiguity
- 0.70-0.84: Ambiguous - classify as "new" unless very clear follow-up indicators
- 0.0-0.69: Clear standalone question - classify as "new"

REWRITING STRATEGY:
1. If follow-up: Expand query with specific terms from context
2. If follow-up: Resolve vague references to concrete entities
3. If follow-up: Include relevant project IDs from recent context
4. If not follow-up: Pass through unchanged

OUTPUT STRICT JSON (no markdown, no code fences):
{{
  "is_followup": boolean,
  "confidence": 0.0-1.0,
  "reasoning": "Why this is/isn't a follow-up based on context analysis",
  "rewritten_query": "Enhanced query with context or original if not followup",
  "filters": {{
    "project_keys": ["ID1", "ID2"],
    "keywords": ["term1", "term2"]
  }},
  "semantic_enrichment": ["topic1", "topic2"]
}}"""

    try:
        response = llm_fast.invoke(prompt).content.strip()
        log_query.info(f"🎯 LLM RESPONSE: {response}")
        
        # Parse JSON response
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)
        except json.JSONDecodeError:
            log_query.error(f"🎯 JSON PARSE ERROR: {response}")
            return user_query, {}
        
        # Enhanced: LLM-based follow-up determination with confidence and reasoning
        confidence = result.get("confidence", 0.0)
        is_followup = result.get("is_followup", False)
        reasoning = result.get("reasoning", "No reasoning provided")
        semantic_enrichment = result.get("semantic_enrichment", [])
        
        log_query.info(f"🧠 LLM ANALYSIS: is_followup={is_followup}, confidence={confidence:.2f}")
        log_query.info(f"🧠 REASONING: {reasoning}")
        if semantic_enrichment:
            log_query.info(f"🧠 SEMANTIC ENRICHMENT: {semantic_enrichment}")
        
        # Process based on LLM's follow-up determination
        if is_followup and confidence >= 0.95:
            rewritten_query = result.get("rewritten_query", user_query)
            filters = result.get("filters", {})
            
            # Enhanced: Handle project keys from filters
            project_keys = filters.get("project_keys", [])
            
            # Fallback logic if LLM didn't identify specific projects
            if not project_keys:
                fallback_projects = focus_state["last_answer_projects"] or focus_state["recent_projects"]
                if fallback_projects:
                    project_keys = fallback_projects[:2]  # Limit to 2 most relevant
                    filters["project_keys"] = project_keys
                    log_query.info(f"🎯 FALLBACK TO CONTEXT PROJECTS: {project_keys}")
            
            log_query.info(f"🎯 FOLLOW-UP DETECTED: '{user_query}' → '{rewritten_query}'")
            log_query.info(f"🎯 ENRICHED WITH: projects={project_keys}, topics={semantic_enrichment}")
        else:
            # Not a follow-up or low confidence - pass through unchanged
            rewritten_query = user_query
            filters = {}
            log_query.info(f"🎯 NON-FOLLOW-UP: Passing through unchanged (confidence={confidence:.2f})")
        
        log_query.info(f"🎯 QUERY REWRITER: {user_query} → {rewritten_query}")
        log_query.info(f"🎯 FILTERS: {filters}")
        
        return rewritten_query, filters
        
    except Exception as e:
        log_query.error(f"🎯 QUERY REWRITER ERROR: {e}")
        return user_query, {}


# =============================================================================
# CONVERSATION CONTEXT FORMATTING
# =============================================================================

def get_conversation_context(session_id: str, max_exchanges: int = 3) -> str:
    """
    Format recent conversation history for inclusion in prompts.
    Returns a formatted string with the last N question-answer pairs, prioritizing most recent.
    
    Args:
        session_id: Session identifier
        max_exchanges: Maximum number of exchanges to include (default: 3)
    
    Returns:
        Formatted conversation history string
    """
    session = SESSION_MEMORY.get(session_id, {})
    history = session.get("conversation_history", [])

    if not history:
        log_query.info("💭 CONVERSATION CONTEXT: No prior history found")
        return ""

    # Get last N exchanges (most recent first internally, but we'll format oldest-to-newest for clarity)
    recent = history[-max_exchanges:]

    # Log what we're retrieving
    log_query.info(
        f"💭 CONVERSATION CONTEXT: Retrieving {len(recent)} of {len(history)} total exchanges "
        f"(prioritizing most recent)"
    )
    for i, exchange in enumerate(recent, 1):
        q = exchange.get("question", "")[:80]  # First 80 chars
        projects = exchange.get("projects", [])
        log_query.info(f"   Exchange {i}: Q: {q}... | Projects: {projects[:3]}")

    lines = [
        "RECENT CONVERSATION HISTORY (last 3 exchanges, ordered oldest to newest):",
        "IMPORTANT: When the user asks a follow-up question, DEFAULT to the MOST RECENT exchange "
        "(the last one below) unless they EXPLICITLY reference an older one.",
        "Examples of explicit references: 'the first question', 'originally', 'earlier we discussed', 'back to...'",
        "If no explicit reference → assume MOST RECENT exchange."
    ]

    for i, exchange in enumerate(recent, 1):
        q = exchange.get("question", "")
        a = exchange.get("answer", "")
        projects = exchange.get("projects", [])

        # Truncate long answers to keep context manageable
        a_truncated = a[:300] + "..." if len(a) > 300 else a

        # Mark the most recent exchange
        is_most_recent = (i == len(recent))
        exchange_label = f"Exchange {i}" + (" (MOST RECENT - DEFAULT CONTEXT)" if is_most_recent else "")

        lines.append(f"\n{exchange_label}:")
        lines.append(f"Q: {q}")
        lines.append(f"A: {a_truncated}")
        if projects:
            lines.append(f"Projects mentioned: {', '.join(projects[:5])}")

    return "\n".join(lines)

