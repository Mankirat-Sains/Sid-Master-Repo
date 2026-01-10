"""
Project resolver: confirm existence of a project via Supabase project_info
and speckle mapping, even when no documents are indexed.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

from supabase import create_client

from config.settings import PROJECT_RE, SUPABASE_KEY, SUPABASE_URL
from config.logging_config import log_query

# Simple in-memory cache so we don't hit Supabase repeatedly for fuzzy lookups
_PROJECT_CACHE: Dict[str, object] = {"rows": None, "ts": 0.0}
_PROJECT_CACHE_TTL = 300  # seconds


def _load_speckle_mapping() -> Dict[str, Dict[str, str]]:
    try:
        mapping_path = Path(__file__).resolve().parent.parent / "references" / "speckle_mapping.json"
        if mapping_path.exists():
            return json.loads(mapping_path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        log_query.warning(f"Failed to load speckle_mapping.json: {exc}")
    return {}


def _get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:  # pragma: no cover - defensive
        log_query.warning(f"Project resolver: failed to create Supabase client: {exc}")
        return None


def _normalize_aliases(raw_aliases) -> List[str]:
    if not raw_aliases:
        return []
    if isinstance(raw_aliases, list):
        return [str(a).strip() for a in raw_aliases if a]
    if isinstance(raw_aliases, str):
        try:
            loaded = json.loads(raw_aliases)
            if isinstance(loaded, list):
                return [str(a).strip() for a in loaded if a]
        except Exception:
            return [raw_aliases.strip()]
    return []


def _load_projects_for_fuzzy(supa) -> List[Dict[str, str]]:
    now = time.time()
    if _PROJECT_CACHE["rows"] and now - _PROJECT_CACHE["ts"] < _PROJECT_CACHE_TTL:
        return _PROJECT_CACHE["rows"]
    if not supa:
        return []
    try:
        resp = (
            supa.table("project_info")
            .select(
                "project_key, project_name, project_address, project_city, project_postal_code, "
                "speckle_project_id, speckle_model_id, alias_names"
            )
            .limit(500)
            .execute()
        )
        rows = resp.data or []
        for row in rows:
            row["alias_names"] = _normalize_aliases(row.get("alias_names"))
        _PROJECT_CACHE["rows"] = rows
        _PROJECT_CACHE["ts"] = now
        return rows
    except Exception as exc:  # pragma: no cover - defensive
        log_query.warning(f"Project resolver: fuzzy load failed: {exc}")
        return []


def _best_fuzzy_match(norm_lower: str, rows: List[Dict[str, str]]) -> Tuple[Optional[Dict[str, str]], float]:
    best_row = None
    best_score = 0.0

    def _score(candidate: str) -> float:
        if not candidate:
            return 0.0
        return SequenceMatcher(None, norm_lower, candidate.lower()).ratio()

    for row in rows:
        names = [row.get("project_key", ""), row.get("project_name", "")]
        names.extend(_normalize_aliases(row.get("alias_names")))
        for name in names:
            s = _score(name)
            if s > best_score:
                best_score = s
                best_row = row
    return best_row, best_score


def resolve_project(name_or_key: str) -> Optional[Dict[str, str]]:
    """
    Resolve a project by key or name using project_info and speckle mapping.
    Returns a metadata dict if found, else None.
    """
    if not name_or_key:
        return None
    norm = " ".join(name_or_key.strip().split())
    norm_lower = norm.lower()

    # Try Supabase project_info (by key/name first, then alias_names contains, then fuzzy)
    meta: Dict[str, str] = {}
    supa = _get_supabase_client()
    if supa:
        try:
            resp = (
                supa.table("project_info")
                .select(
                    "project_key, project_name, project_address, project_city, project_postal_code, "
                    "speckle_project_id, speckle_model_id, alias_names"
                )
                .or_(f"project_key.ilike.%{norm}%,project_name.ilike.%{norm}%")
                .limit(1)
                .execute()
            )
            row = resp.data[0] if resp.data else None
            if row:
                meta.update(
                    {
                        "project_key": row.get("project_key") or "",
                        "project_name": row.get("project_name") or "",
                        "project_address": row.get("project_address") or "",
                        "project_city": row.get("project_city") or "",
                        "project_postal_code": row.get("project_postal_code") or "",
                        "speckle_project_id": row.get("speckle_project_id") or "",
                        "speckle_model_id": row.get("speckle_model_id") or "",
                        "alias_names": _normalize_aliases(row.get("alias_names")),
                    }
                )
        except Exception as exc:  # pragma: no cover - defensive
            log_query.warning(f"Project resolver: Supabase lookup failed: {exc}")

    # Try alias_names JSONB (array contains). This avoids needing project_aliases table.
    if not meta and supa:
        try:
            alias_resp = (
                supa.table("project_info")
                .select(
                    "project_key, project_name, project_address, project_city, project_postal_code, "
                    "speckle_project_id, speckle_model_id, alias_names"
                )
                .contains("alias_names", [norm])
                .limit(1)
                .execute()
            )
            alias_row = alias_resp.data[0] if alias_resp.data else None
            if alias_row:
                meta = {
                    "project_key": alias_row.get("project_key") or "",
                    "project_name": alias_row.get("project_name") or "",
                    "project_address": alias_row.get("project_address") or "",
                    "project_city": alias_row.get("project_city") or "",
                    "project_postal_code": alias_row.get("project_postal_code") or "",
                    "speckle_project_id": alias_row.get("speckle_project_id") or "",
                    "speckle_model_id": alias_row.get("speckle_model_id") or "",
                    "alias_names": _normalize_aliases(alias_row.get("alias_names")),
                }
        except Exception as exc:  # pragma: no cover - defensive
            log_query.warning(f"Project resolver: alias_names lookup failed: {exc}")

    # If still no match, try fuzzy match over project_info rows (project_name, project_key, alias_names)
    if not meta and supa:
        rows = _load_projects_for_fuzzy(supa)
        fuzzy_row, score = _best_fuzzy_match(norm_lower, rows)
        if fuzzy_row and score >= 0.62:  # threshold tuned to allow partial names without overmatching
            meta = {
                "project_key": fuzzy_row.get("project_key") or "",
                "project_name": fuzzy_row.get("project_name") or "",
                "project_address": fuzzy_row.get("project_address") or "",
                "project_city": fuzzy_row.get("project_city") or "",
                "project_postal_code": fuzzy_row.get("project_postal_code") or "",
                "speckle_project_id": fuzzy_row.get("speckle_project_id") or "",
                "speckle_model_id": fuzzy_row.get("speckle_model_id") or "",
                "alias_names": _normalize_aliases(fuzzy_row.get("alias_names")),
                "match_score": score,
            }

    # Speckle mapping
    mapping = _load_speckle_mapping()
    # Exact hits
    speckle = mapping.get(norm) or mapping.get(meta.get("project_key", ""))
    # Fuzzy contains on keys/names when no exact hit
    if not speckle:
        for key, val in mapping.items():
            key_lower = key.lower()
            name_lower = str(val.get("name", "")).lower()
            if norm_lower in key_lower or norm_lower in name_lower or key_lower in norm_lower:
                speckle = val
                break

    if speckle:
        meta.setdefault("project_key", speckle.get("name") or norm)
        meta.setdefault("project_name", speckle.get("name") or norm)
        meta["speckle_project_id"] = speckle.get("projectId") or ""
        meta["speckle_model_id"] = speckle.get("modelId") or ""

    if meta:
        return meta
    return None


def extract_project_keys(text: str) -> Dict[str, str]:
    """
    Extract probable project keys/names from free text using PROJECT_RE and naive splits.
    Returns a dict {candidate: candidate}.
    """
    candidates: Dict[str, str] = {}
    if not text:
        return candidates
    # Regex-based keys (e.g., 25-01-180)
    for match in PROJECT_RE.finditer(text):
        candidates[match.group(0)] = match.group(0)
    # Quoted names
    for match in re.finditer(r'"([^"]+)"', text):
        val = match.group(1).strip()
        if val:
            candidates[val] = val
    # Fallback: whole text
    stripped = text.strip()
    if stripped and stripped not in candidates:
        candidates[stripped] = stripped
    return candidates
