"""
Session Memory & Focus State Management
Handles conversation history, follow-up detection, and query rewriting
"""
import re
import json
from typing import Dict, TypedDict, Optional, Tuple, List

# Import configurations and LLM instances
from config.llm_instances import llm_fast
from config.settings import MAX_CONVERSATION_HISTORY, MAX_SEMANTIC_HISTORY

# Import logging
from config.logging_config import log_query
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

def intelligent_query_rewriter(
    user_query: str, 
    session_id: str,
    messages: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, dict]:
    """
    Use LLM to intelligently rewrite queries and detect follow-ups.
    Handles pronoun resolution, follow-up detection, and context expansion.
    
    Args:
        user_query: The user's raw query
        session_id: Session identifier for context retrieval
        messages: Optional messages from state (preferred over SESSION_MEMORY)
                  Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Returns:
        Tuple of (rewritten_query, filters_dict)
    """
    # Guardrail: Only extract explicit project IDs if user explicitly types them in the query
    # This is fine - user is being explicit, not a follow-up
    explicit_ids = re.findall(r'\b\d{2}-\d{2}-\d{3,4}\b', user_query)
    if explicit_ids:
        log_query.info(f"🎯 EXPLICIT IDs DETECTED IN QUERY: {explicit_ids}")
        return user_query, {"project_keys": explicit_ids}
    
    # Use messages from state if provided (preferred), otherwise fall back to SESSION_MEMORY
    if messages is None:
        session_data = SESSION_MEMORY.get(session_id, {})
        # Try to get messages, fallback to conversation_history for backward compatibility
        messages = session_data.get("messages", [])
        if not messages and session_data.get("conversation_history"):
            # Convert old format to new format for backward compatibility
            messages = []
            for exchange in session_data["conversation_history"]:
                messages.append({"role": "user", "content": exchange.get("question", "")})
                messages.append({"role": "assistant", "content": exchange.get("answer", "")})
        log_query.info(f"💭 Using messages from SESSION_MEMORY ({len(messages)} messages)")
    else:
        log_query.info(f"💭 Using messages from state ({len(messages)} messages)")
    
    # SEMANTIC INTELLIGENCE: Get semantic context from session memory (for semantic patterns)
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_context = _extract_semantic_context_for_rewriter(session_data)
    
    # Format FULL conversation history for LLM (user sees this, so LLM should see it too)
    # Show complete messages - this is what the user actually sees
    conversation_context_str = ""
    if messages:
        conversation_context_str = "\n\nFULL CONVERSATION HISTORY (what the user sees):\n"
        # Show all messages (or last 10 exchanges if too long)
        max_exchanges = 10
        max_messages = max_exchanges * 2
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        exchange_num = 1
        for i in range(0, len(recent_messages), 2):
            if i + 1 < len(recent_messages):
                user_msg = recent_messages[i]
                assistant_msg = recent_messages[i + 1]
                if user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant":
                    q = user_msg.get("content", "")
                    a = assistant_msg.get("content", "")  # Full answer - user sees this!
                    conversation_context_str += f"\n--- Exchange {exchange_num} ---\n"
                    conversation_context_str += f"USER: {q}\n"
                    conversation_context_str += f"ASSISTANT: {a}\n"
                    exchange_num += 1
            elif i < len(recent_messages):
                # Handle case where we have a user message but no assistant response yet
                user_msg = recent_messages[i]
                if user_msg.get("role") == "user":
                    q = user_msg.get("content", "")
                    conversation_context_str += f"\n--- Exchange {exchange_num} (in progress) ---\n"
                    conversation_context_str += f"USER: {q}\n"
                    exchange_num += 1
    
    prompt = f"""You are an intelligent query processor for an engineering-drawings RAG system. Your job is to understand the FULL SEMANTIC CONTEXT of the conversation and rewrite queries to be self-contained and complete.

CURRENT QUERY: "{user_query}"
{conversation_context_str}

SEMANTIC INTELLIGENCE:
- Recent topics explored: {semantic_context["recent_topics"]}
- Recent complexity patterns: {semantic_context["recent_complexity_patterns"]}  
- Last route preference: {semantic_context["last_route"]}
- Last scope pattern: {semantic_context["last_scope"]}

CRITICAL: The conversation history above is EXACTLY what the user sees. Use it to understand the full context of what was discussed.

YOUR TASK: Understand the semantic context and rewrite the query intelligently.

STEP 1: CONTEXT UNDERSTANDING
Read the conversation history and understand:
- What topics were discussed?
- What projects were mentioned? (Project IDs are in format "25-XX-XXX" or "25-XX-XXXX")
- What specific aspects were covered? (foundations, structural systems, materials, etc.)
- What was the user's original intent?
- What information was provided in the assistant's responses?

STEP 2: FOLLOW-UP DETECTION
Determine if the current query is a follow-up to previous conversation.

FOLLOW-UP EXAMPLES (not exhaustive - be intelligent):
- "tell me more" → wants more detail about what was just discussed
- "find me more samples" → wants more examples of what was just discussed
- "why do you think that is" → asking for reasoning about previous answer
- "what about the foundation" → asking about a specific aspect mentioned before
- "can you elaborate" → wants more detail on previous answer
- "the last project" → referring to a project from previous response
- "the first one" → referring to first item from previous response
- "it", "that", "those" → referring to something from previous conversation
- Any query that is incomplete or unclear without prior context

NON-FOLLOW-UP EXAMPLES:
- Complete, self-contained questions that make sense independently
- New topics unrelated to recent conversation
- Explicit project IDs in current query (user is being explicit, not referencing)

STEP 3: INTELLIGENT QUERY REWRITING
If this is a follow-up, rewrite the query to be SELF-CONTAINED with all necessary context:

EXAMPLES:
- User: "tell me more" (after discussing floating slabs)
  → Rewritten: "Provide detailed information about floating slab foundation systems, including design specifications, reinforcement details, and construction methods"

- User: "the last project" (after listing 3 projects: 25-01-064, 25-01-070, 25-01-028)
  → Rewritten: "Provide comprehensive details about project 25-01-028 including all structural systems, foundation details, and design specifications"

- User: "why do you think that is" (after discussing foundation types)
  → Rewritten: "Explain the reasoning and engineering principles behind the foundation type recommendations and design decisions discussed"

- User: "find me more samples" (after showing floating slab projects)
  → Rewritten: "Find additional engineering projects with floating slab foundation systems, including design details and specifications"

KEY PRINCIPLES:
1. The rewritten query should be COMPLETE and SELF-CONTAINED - someone reading only the rewritten query should understand what to search for
2. Include ALL relevant context from the conversation (topics, projects, aspects discussed)
3. Resolve all pronouns and vague references to concrete entities
4. If the user asks "tell me more", expand it to include what "more" means based on context
5. If the user asks "why", expand it to include what they're asking "why" about

STEP 4: FILTER EXTRACTION
As part of understanding context, extract any filters that would help narrow the search:
- project_keys: Project IDs mentioned in conversation that are relevant to this query
- keywords: Important terms from the conversation that should be emphasized

IMPORTANT:
- Only extract project_keys if they are clearly relevant to what the user is asking about
- If the user says "tell me more" about a specific project, include that project ID
- If the user asks a general follow-up, you may not need project_keys (let the rewritten query handle it)
- Keywords should capture the semantic essence of what was discussed

CONFIDENCE GUIDELINES:
- 0.95-1.0: Strong evidence of follow-up (pronouns, "tell me more", "why", etc.)
- 0.85-0.94: Clear evidence but some ambiguity
- 0.70-0.84: Ambiguous - classify as "new" unless very clear follow-up indicators
- 0.0-0.69: Clear standalone question - classify as "new"

OUTPUT STRICT JSON (no markdown, no code fences):
{{
  "is_followup": boolean,
  "confidence": 0.0-1.0,
  "reasoning": "Your analysis of the context and why this is/isn't a follow-up",
  "rewritten_query": "A complete, self-contained query that includes all necessary context. Should be intelligible without reading the conversation history.",
  "filters": {{
    "project_keys": ["25-XX-XXX"],  // Only if clearly relevant to the query
    "keywords": ["term1", "term2"]  // Important semantic terms from context
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
        # Trust the LLM's judgment - it has the full conversation context
        confidence_threshold = 0.85
        
        if is_followup and confidence >= confidence_threshold:
            rewritten_query = result.get("rewritten_query", user_query)
            filters = result.get("filters", {})
            
            # Trust LLM's project_keys extraction - it read the conversation history
            project_keys = filters.get("project_keys", [])
            
            if project_keys:
                log_query.info(f"🎯 LLM EXTRACTED PROJECTS FROM CONVERSATION: {project_keys}")
            else:
                log_query.info(f"🎯 LLM DETECTED FOLLOW-UP BUT NO PROJECTS IDENTIFIED (may be ambiguous reference)")
            
            log_query.info(f"🎯 FOLLOW-UP DETECTED: '{user_query}' → '{rewritten_query}'")
            log_query.info(f"🎯 ENRICHED WITH: projects={project_keys}, topics={semantic_enrichment}")
        else:
            # Not a follow-up or low confidence - pass through unchanged
            rewritten_query = user_query
            filters = {}
            log_query.info(f"🎯 NON-FOLLOW-UP: Passing through unchanged (confidence={confidence:.2f}, threshold={confidence_threshold:.2f})")
        
        log_query.info(f"🎯 QUERY REWRITER: {user_query} → {rewritten_query}")
        log_query.info(f"🎯 FILTERS: {filters}")
        
        return rewritten_query, filters
        
    except Exception as e:
        log_query.error(f"🎯 QUERY REWRITER ERROR: {e}")
        return user_query, {}


# =============================================================================
# CONVERSATION CONTEXT FORMATTING
# =============================================================================

def get_conversation_context(session_id: str, max_exchanges: int = 3, messages: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Format recent messages for inclusion in prompts.
    Returns a formatted string with the last N question-answer pairs, prioritizing most recent.
    
    Args:
        session_id: Session identifier (for backward compatibility)
        max_exchanges: Maximum number of exchanges to include (default: 3)
        messages: Optional messages from state (preferred over SESSION_MEMORY)
                  Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Returns:
        Formatted conversation history string
    """
    # Use state messages if provided (from checkpointer), otherwise fall back to SESSION_MEMORY
    if messages is not None:
        msg_list = messages
        log_query.info(f"💭 Using messages from state ({len(msg_list)} messages)")
    else:
        session = SESSION_MEMORY.get(session_id, {})
        # Try messages first, fallback to conversation_history for backward compatibility
        msg_list = session.get("messages", [])
        if not msg_list and session.get("conversation_history"):
            # Convert old format to new format
            msg_list = []
            for exchange in session["conversation_history"]:
                msg_list.append({"role": "user", "content": exchange.get("question", "")})
                msg_list.append({"role": "assistant", "content": exchange.get("answer", "")})
        log_query.info(f"💭 Using messages from SESSION_MEMORY ({len(msg_list)} messages)")

    if not msg_list:
        log_query.info("💭 CONVERSATION CONTEXT: No prior messages found")
        return ""

    # Get last N exchanges (each exchange = 2 messages: user + assistant)
    max_messages = max_exchanges * 2
    recent_messages = msg_list[-max_messages:]

    # Log what we're retrieving
    num_exchanges = len(recent_messages) // 2
    log_query.info(
        f"💭 CONVERSATION CONTEXT: Retrieving {num_exchanges} exchanges from {len(msg_list)} total messages "
        f"(prioritizing most recent)"
    )
    
    # Format messages as exchanges
    # Show FULL conversation history - user sees this, so LLM should see it too
    lines = [
        f"FULL CONVERSATION HISTORY (what the user sees, showing last {max_exchanges} exchanges, ordered oldest to newest):",
        "IMPORTANT: When the user asks a follow-up question, DEFAULT to the MOST RECENT exchange "
        "(the last one below) unless they EXPLICITLY reference an older one.",
        "Examples of explicit references: 'the first question', 'originally', 'earlier we discussed', 'back to...'",
        "If no explicit reference → assume MOST RECENT exchange.",
        "CRITICAL: Read the FULL conversation to understand what 'this', 'it', 'the third project', etc. refers to."
    ]
    
    exchange_num = 1
    for i in range(0, len(recent_messages), 2):
        if i + 1 < len(recent_messages):
            user_msg = recent_messages[i]
            assistant_msg = recent_messages[i + 1]
            if user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant":
                q = user_msg.get("content", "")
                a = assistant_msg.get("content", "")
                
                # Extract projects from answer using regex
                PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')
                projects = []
                for match in PROJECT_RE.finditer(a):
                    proj_id = match.group(0)
                    if proj_id not in projects:
                        projects.append(proj_id)
                
                # Show full answer - user sees this, so LLM should see it too
                # Don't truncate - we need full context for intelligent understanding
                a_truncated = a
                
                # Mark the most recent exchange
                is_most_recent = (exchange_num == num_exchanges)
                exchange_label = f"Exchange {exchange_num}" + (" (MOST RECENT - DEFAULT CONTEXT)" if is_most_recent else "")
                
                lines.append(f"\n{exchange_label}:")
                lines.append(f"Q: {q}")
                lines.append(f"A: {a_truncated}")
                if projects:
                    lines.append(f"Projects mentioned: {', '.join(projects[:5])}")
                
                # Log what we're retrieving
                log_query.info(f"   Exchange {exchange_num}: Q: {q[:80]}... | Projects: {projects[:3]}")
                
                exchange_num += 1
    
    return "\n".join(lines)

