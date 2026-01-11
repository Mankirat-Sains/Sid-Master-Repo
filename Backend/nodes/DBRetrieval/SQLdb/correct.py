"""
Correction Node
Applies corrections to answers if needed
Also updates conversation history (runs last, has access to final answers)
"""
import time
import re
from models.rag_state import RAGState
from config.settings import MAX_CONVERSATION_HISTORY
from config.logging_config import log_enh

USE_SUPPORT_SCORING = False  # Disable support scoring for performance

# Project ID regex for extracting projects from answers
PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')


def node_correct(state: RAGState, max_hops: int = 1, min_score: float = 0.6) -> dict:
    """Simplified corrective step - optionally calculate support score"""
    t_start = time.time()
    log_enh.info(">>> CORRECT START")
    
    # Preserve follow-up questions and suggestions from verify node
    result = {
        "follow_up_questions": getattr(state, 'follow_up_questions', []) or [],
        "follow_up_suggestions": getattr(state, 'follow_up_suggestions', []) or []
    }
    
    log_enh.info(f"Preserving follow-up questions: {len(result['follow_up_questions'])} questions, {len(result['follow_up_suggestions'])} suggestions")

    if state.corrective_attempted:
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< CORRECT DONE (already attempted) in {t_elapsed:.2f}s")
        return result

    # Calculate support score only if enabled
    # Note: support_score function not extracted (disabled by default)
    if USE_SUPPORT_SCORING:
        try:
            from utils.support_scoring import support_score
            score = support_score(state.user_query, state.final_answer or "", state.graded_docs)
            log_enh.info(f"Support score: {score:.2f}")
        except ImportError:
            log_enh.warning("Support scoring enabled but support_score function not found")
            score = 1.0
    else:
        score = 1.0  # Default to 1.0 when scoring is disabled
        log_enh.info(f"Support scoring disabled - using default score: {score:.2f}")

    result.update({
        "answer_support_score": score,
        "corrective_attempted": True
    })
    
    # Update messages (persisted by checkpointer) - Follows LangGraph's simple pattern
    # This node runs last, so we have access to final_answer, code_answer, coop_answer
    # CRITICAL: The user message is already in state.messages (added in main.py before graph.invoke)
    # We only need to add the assistant message here
    messages = list(state.messages or [])
    
    # Build full answer text
    answer_text = state.final_answer or ""
    if state.code_answer:
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{state.code_answer}"
    if state.coop_answer:
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{state.coop_answer}"
    
    # Add assistant message (user message is already in state from main.py)
    if answer_text:
        # Check if the last message is already an assistant message (shouldn't happen, but safety check)
        if messages and messages[-1].get("role") == "assistant":
            # Replace the last assistant message (in case this is a retry)
            messages[-1] = {
                "role": "assistant",
                "content": answer_text
            }
            log_enh.info("💾 Replaced existing assistant message")
        else:
            # Add new assistant message
            messages.append({
                "role": "assistant",
                "content": answer_text
            })
            log_enh.info("💾 Added new assistant message")
        
        # Maintain sliding window (keep last MAX_CONVERSATION_HISTORY * 2 messages since each exchange is 2 messages)
        max_messages = MAX_CONVERSATION_HISTORY * 2
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
            log_enh.info(f"💾 Messages sliding window: kept last {max_messages} messages ({MAX_CONVERSATION_HISTORY} exchanges)")
        
        result["messages"] = messages
        log_enh.info(f"💾 Updated messages: {len(messages)} messages ({len(messages) // 2} exchanges)")
    else:
        # No answer yet, just preserve existing messages
        result["messages"] = messages
        log_enh.info(f"💾 No answer yet, preserving {len(messages)} messages")

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< CORRECT DONE in {t_elapsed:.2f}s")

    return result

