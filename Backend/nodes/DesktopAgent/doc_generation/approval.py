"""
Section approval helpers for doc generation.
"""
from __future__ import annotations
import os
from typing import List, Dict


AUTO_APPROVE_SECTIONS = os.getenv("AUTO_APPROVE_SECTIONS", "").lower() in {"1", "true", "yes", "on"}


def _normalize_status(status: str | None) -> str:
    status = (status or "").lower()
    if status in {"approved", "draft", "rejected", "pending", "locked"}:
        return status
    return "pending"


def approve_section(section_queue: List[Dict], section_id: str) -> List[Dict]:
    """
    Mark section_id as approved and unlock the next locked section (set to pending).
    """
    updated = []
    unlock_next = False
    for sec in section_queue:
        if not isinstance(sec, dict):
            continue
        entry = dict(sec)
        status = _normalize_status(entry.get("status"))
        if entry.get("section_id") == section_id:
            entry["status"] = "approved"
            unlock_next = True
        elif unlock_next and status == "locked":
            entry["status"] = "pending"
            unlock_next = False
        updated.append(entry)
    return updated


def reject_section(section_queue: List[Dict], section_id: str, feedback: str | None = None) -> List[Dict]:
    """
    Mark section_id as rejected; keep others unchanged.
    """
    updated = []
    for sec in section_queue:
        if not isinstance(sec, dict):
            continue
        entry = dict(sec)
        if entry.get("section_id") == section_id:
            entry["status"] = "rejected"
            if feedback:
                entry["feedback"] = feedback
        updated.append(entry)
    return updated


def maybe_auto_approve(section_queue: List[Dict], section_id: str) -> List[Dict]:
    """
    Auto-approve the current section and unlock the next one when the test flag is enabled.
    No-op when AUTO_APPROVE_SECTIONS is false.
    """
    if not AUTO_APPROVE_SECTIONS or not section_queue or not section_id:
        return section_queue
    return approve_section(section_queue, section_id)
