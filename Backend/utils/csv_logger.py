"""
CSV logger for doc generation outputs.
Best-effort file locking (fcntl when available).
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def _lock_file(fh):
    try:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        return True
    except Exception:
        return False


def _unlock_file(fh):
    try:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass


def append_draft_csv(
    csv_path: str,
    request: str,
    doc_type: str | None,
    section_type: str | None,
    min_chars: int | None,
    max_chars: int | None,
    length_actual: int,
    draft_text: str,
    citations: List[Dict],
    execution_trace: List[str],
    warnings: List[str],
) -> None:
    path = Path(csv_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "request",
        "doc_type",
        "section_type",
        "min_chars",
        "max_chars",
        "length_actual",
        "draft_text",
        "citations_json",
        "execution_trace_json",
        "warnings_json",
    ]
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": request,
        "doc_type": doc_type or "",
        "section_type": section_type or "",
        "min_chars": min_chars if min_chars is not None else "",
        "max_chars": max_chars if max_chars is not None else "",
        "length_actual": length_actual,
        "draft_text": draft_text,
        "citations_json": json.dumps(citations or []),
        "execution_trace_json": json.dumps(execution_trace or []),
        "warnings_json": json.dumps(warnings or []),
    }
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        locked = _lock_file(fh)
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
        if locked:
            _unlock_file(fh)

