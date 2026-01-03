"""
Project ID Utilities
Functions for parsing, validating, and working with project IDs
"""
import re
import datetime as _dt
from typing import List, Optional
from collections import defaultdict
from langchain_core.documents import Document
from config.settings import PROJECT_RE
from config.logging_config import log_query

_PROJECT_ID_RE = re.compile(r"\b(?P<yy>\d{2})-(?P<mm>\d{2})-(?P<seq>\d{3})\b")


def detect_project_filter(q: str) -> Optional[str]:
    """
    Extract and normalize project ID from query with STRICT exact matching.
    Handles formats: 25-08-005, 2508005, 25/08/005, etc.
    Returns: Normalized format YY-MM-XXX (e.g., "25-08-005") ONLY if exact match
    """
    patterns = [
        r'\b(\d{2})-(\d{2})-(\d{3})\b',  # 25-08-005 format
        r'\b(\d{2})/(\d{2})/(\d{3})\b',  # 25/08/005 format
        r'\b(\d{2})\.(\d{2})\.(\d{3})\b', # 25.08.005 format
        r'\b(\d{7})\b',                   # 2508005 format (7 digits)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            if len(match.groups()) == 3:  # Format with separators
                year, month, index = match.groups()
                if (0 <= int(year) <= 99 and 
                    1 <= int(month) <= 12 and 
                    1 <= int(index) <= 999):
                    normalized = f"{year}-{month}-{index}"
                    log_query.info(f"🎯 PROJECT DETECTION: Exact match '{match.group(0)}' → '{normalized}'")
                    return normalized
            elif len(match.groups()) == 1:  # 7-digit format
                digits = match.group(1)
                year, month, index = digits[:2], digits[2:4], digits[4:]
                if (0 <= int(year) <= 99 and 
                    1 <= int(month) <= 12 and 
                    1 <= int(index) <= 999):
                    normalized = f"{year}-{month}-{index}"
                    log_query.info(f"🎯 PROJECT DETECTION: Exact match '{digits}' → '{normalized}'")
                    return normalized
    
    log_query.info(f"🎯 PROJECT DETECTION: No exact project ID found in '{q}'")
    return None


def date_from_project_id(pid: str) -> Optional[_dt.date]:
    """
    Parse 'YY-MM-XXX' → date(2000+YY, MM, 1).
    Returns None if it doesn't look like a project id.
    """
    m = _PROJECT_ID_RE.fullmatch(pid or "")
    if not m:
        return None
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    year = 2000 + yy
    if not (1 <= mm <= 12):
        return None
    return _dt.date(year, mm, 1)


def requested_project_count(q: str) -> Optional[int]:
    """Extract explicit project count from query"""
    _WORD_TO_NUM = {
        "one":1,"two":2,"three":3,"four":4,"five":5,
        "six":6,"seven":7,"eight":8,"nine":9,"ten":10
    }
    
    ql = q.lower()
    # numeric like "3 projects" / "top 3" / "give me 3"
    m = re.search(r'\b(?:top\s*)?(\d{1,2})\b\s*(?:projects?|examples?)', ql)
    if m: 
        return int(m.group(1))
    # words like "three projects"
    for w, n in _WORD_TO_NUM.items():
        if re.search(rf'\b{w}\b\s*(?:projects?|examples?)', ql):
            return n
    return None


def _infer_n_from_q(q: str, default_n: int = 5) -> int:
    """Intelligently infer project count from question using LLM"""
    # First try the existing pattern matching for explicit numbers
    explicit_n = requested_project_count(q)
    if explicit_n:
        log_query.info(f"🎯 PROJECT LIMIT: Found explicit number in query: {explicit_n}")
        return explicit_n
    
    # If no explicit number, use LLM to understand intent
    smart_limit = -1
    if smart_limit == -1:
        final_limit = -1  # Unlimited
    elif smart_limit > 0:
        final_limit = -1  # Specific number
    else:
        final_limit = default_n  # Fallback (0 or other)
    log_query.info(f"🎯 PROJECT LIMIT: Final limit determined: {final_limit}")
    return final_limit


def _group_by_project_all(docs: List[Document]):
    """Group documents by project"""
    m, order = {}, []
    for d in docs:
        md = d.metadata or {}
        p = md.get("drawing_number") or md.get("project_key")
        if not p:
            m_ = PROJECT_RE.search(d.page_content or "")
            p = m_.group(0) if m_ else None
        if not p: 
            continue
        if p not in m:
            m[p] = []
            order.append(p)
        m[p].append(d)
    return m, order


def _rank_projects_by_recency(docs: List[Document]) -> List[str]:
    """Rank projects by date (newest first)"""
    proj_to_docs, _ = _group_by_project_all(docs)
    scored = []
    for p, chunks in proj_to_docs.items():
        md = chunks[0].metadata or {}
        y, m, d = 0, 0, 0
        for k in ("date", "issue_date", "signed_date"):
            v = md.get(k)
            if v:
                nums = re.findall(r"\d+", v)
                if len(nums) >= 2:
                    y, m = int(nums[0]), int(nums[1])
                    d = int(nums[2]) if len(nums) > 2 else 1
                    break
        if (y, m) == (0, 0):
            dt = date_from_project_id(p)
            if dt:
                y, m, d = dt.year, dt.month, dt.day
        scored.append(((y, m, d), p))
    scored.sort(reverse=True)
    return [p for _, p in scored]


def _rank_projects_by_accuracy_then_recency(docs: List[Document]) -> List[str]:
    """Rank projects by average similarity (higher = better)"""
    proj_scores = {}

    for d in docs:
        metadata = d.metadata or {}
        project = metadata.get("drawing_number") or metadata.get("project_key")
        if not project:
            continue

        sim = metadata.get("similarity_score", 0.0)
        if project not in proj_scores:
            proj_scores[project] = []
        proj_scores[project].append(sim)

    # Average similarity per project
    scored = [(sum(sims) / len(sims), proj) for proj, sims in proj_scores.items()]
    scored.sort(reverse=True)  # higher similarity = better ranking

    ranked_projects = [proj for _, proj in scored]
    log_query.info(f"🎯 SIMPLE RANKING: Final project order (by similarity): {ranked_projects}")
    return ranked_projects


def _limit_docs_to_projects(docs: List[Document], projects: List[str], per_project_cap: int = 3) -> List[Document]:
    """Limit documents to specific projects with per-project cap"""
    proj_to_docs, _ = _group_by_project_all(docs)
    out = []
    for p in projects:
        out += (proj_to_docs.get(p, [])[:per_project_cap])
    return out

