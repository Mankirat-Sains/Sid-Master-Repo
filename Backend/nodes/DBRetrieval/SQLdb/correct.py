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
    
    # Update conversation history (persisted by checkpointer)
    # This node runs last, so we have access to final_answer, code_answer, coop_answer
    conversation_history = list(state.conversation_history or [])
    
    # Build full answer text
    answer_text = state.final_answer or ""
    if state.code_answer:
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{state.code_answer}"
    if state.coop_answer:
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{state.coop_answer}"
    
    # Extract projects from answer text
    projects_in_answer = []
    seen = set()
    for match in PROJECT_RE.finditer(answer_text):
        proj_id = match.group(0)
        if proj_id not in seen:
            projects_in_answer.append(proj_id)
            seen.add(proj_id)
    
    # Add new exchange to conversation history
    # Use original_question if available (user's actual question), otherwise fall back to user_query (rewritten)
    question_to_store = getattr(state, 'original_question', None) or state.user_query
    if question_to_store and answer_text:
        new_exchange = {
            "question": question_to_store,
            "answer": answer_text,
            "timestamp": time.time(),
            "projects": projects_in_answer
        }
        conversation_history.append(new_exchange)
        
        # Maintain sliding window
        if len(conversation_history) > MAX_CONVERSATION_HISTORY:
            conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
            log_enh.info(f"💾 Conversation history sliding window: kept last {MAX_CONVERSATION_HISTORY} exchanges")
        
        result["conversation_history"] = conversation_history
        log_enh.info(f"💾 Updated conversation_history: {len(conversation_history)} exchanges")

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< CORRECT DONE in {t_elapsed:.2f}s")

    return result

