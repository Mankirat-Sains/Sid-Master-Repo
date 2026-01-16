"""
Section approval helpers for doc generation.
"""
from __future__ import annotations
from typing import List, Dict


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
