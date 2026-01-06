"""
Correction Node
Applies corrections to answers if needed
"""
import time
from models.rag_state import RAGState
from config.logging_config import log_enh

USE_SUPPORT_SCORING = False  # Disable support scoring for performance


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

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< CORRECT DONE in {t_elapsed:.2f}s")

    return result

