"""
Correction Node
Applies corrections to answers if needed
Also updates conversation history (runs last, has access to final answers)
"""
import time
import re
from models.db_retrieval_state import DBRetrievalState
from config.settings import MAX_CONVERSATION_HISTORY
from config.logging_config import log_enh

USE_SUPPORT_SCORING = False  # Disable support scoring for performance

# Project ID regex for extracting projects from answers
PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')


def node_correct(state: DBRetrievalState, max_hops: int = 1, min_score: float = 0.6) -> dict:
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
    
    # Build full answer text
    answer_text = state.final_answer or ""
    if state.code_answer:
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{state.code_answer}"
    if state.coop_answer:
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{state.coop_answer}"

    # Capture projects in answer for metadata
    projects_in_answer = []
    for match in PROJECT_RE.finditer(answer_text):
        proj_id = match.group(0)
        if proj_id not in projects_in_answer:
            projects_in_answer.append(proj_id)

    # Normalize existing history into message form for syncing
    raw_history = list(state.conversation_history or [])
    history_as_messages = []
    for entry in raw_history:
        if isinstance(entry, dict) and entry.get("role"):
            msg = {
                "role": entry.get("role"),
                "content": entry.get("content", ""),
            }
            if entry.get("projects") is not None:
                msg["projects"] = entry.get("projects")
            meta = dict(entry.get("metadata") or {})
            ts = entry.get("timestamp")
            if ts is not None and "timestamp" not in meta:
                meta["timestamp"] = ts
            if meta:
                msg["metadata"] = meta
            history_as_messages.append(msg)
            continue

        if isinstance(entry, dict):
            ts = entry.get("timestamp")
            meta = dict(entry.get("metadata") or {})
            question = entry.get("question")
            answer = entry.get("answer")

            if question:
                user_msg = {"role": "user", "content": question}
                if ts is not None:
                    user_meta = {"timestamp": ts}
                    user_msg["metadata"] = user_meta
                history_as_messages.append(user_msg)

            if answer:
                if ts is not None and "timestamp" not in meta:
                    meta["timestamp"] = ts
                assistant_msg = {"role": "assistant", "content": answer}
                if entry.get("projects") is not None:
                    assistant_msg["projects"] = entry.get("projects")
                if meta:
                    assistant_msg["metadata"] = meta
                history_as_messages.append(assistant_msg)

    # Seed messages from state.messages or normalized history
    messages = list(state.messages or []) or list(history_as_messages)
    # Ensure the latest user message is present (main flow appends before graph.invoke)
    if state.original_question and (not messages or messages[-1].get("role") != "user"):
        messages.append({"role": "user", "content": state.original_question})

    # Add assistant message (user message is already in state from main.py)
    assistant_timestamp = time.time()
    if answer_text:
        assistant_metadata = {"support_score": score, "timestamp": assistant_timestamp}
        assistant_message = {
            "role": "assistant",
            "content": answer_text,
            "projects": projects_in_answer,
            "metadata": assistant_metadata,
        }

        # Check if the last message is already an assistant message (retry safety)
        if messages and messages[-1].get("role") == "assistant":
            messages[-1] = assistant_message
            log_enh.info("💾 Replaced existing assistant message")
        else:
            messages.append(assistant_message)
            log_enh.info("💾 Added new assistant message")

    # Maintain sliding window for messages (keep last MAX_CONVERSATION_HISTORY * 2)
    max_messages = MAX_CONVERSATION_HISTORY * 2
    if len(messages) > max_messages:
        messages = messages[-max_messages:]
        log_enh.info(f"💾 Messages sliding window: kept last {max_messages} messages ({MAX_CONVERSATION_HISTORY} exchanges)")

    result["messages"] = messages
    log_enh.info(f"💾 Updated messages: {len(messages)} messages ({len(messages) // 2} exchanges)")

    # Update structured conversation_history for checkpointer persistence
    history = list(raw_history)
    if state.original_question or answer_text:
        if history and isinstance(history[-1], dict):
            last = history[-1]
            if last.get("question") == (state.original_question or state.user_query) and not last.get("answer"):
                history.pop()
        history_entry = {
            "question": state.original_question or state.user_query,
            "answer": answer_text,
            "timestamp": assistant_timestamp,
            "projects": projects_in_answer,
            "metadata": {"support_score": score},
        }
        history.append(history_entry)
        if len(history) > MAX_CONVERSATION_HISTORY:
            history = history[-MAX_CONVERSATION_HISTORY:]
        result["conversation_history"] = history
        log_enh.info(f"💾 Conversation history updated: {len(history)} exchanges")
    else:
        result["conversation_history"] = history
        log_enh.info(f"💾 No answer yet, preserving {len(history)} conversation history entries")

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< CORRECT DONE in {t_elapsed:.2f}s")

    return result
