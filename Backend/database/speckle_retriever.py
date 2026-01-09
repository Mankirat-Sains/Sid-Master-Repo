"""
Speckle Mapping Retriever
Lightweight helper to look up Speckle project/model IDs from a shared JSON mapping.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from config.logging_config import log_query

MAPPING_PATH = Path(__file__).resolve().parent.parent / "references" / "speckle_mapping.json"


def _normalize_key(project_key: str) -> str:
    """Normalize project key/name for lookup."""
    return (project_key or "").strip()


@lru_cache(maxsize=1)
def _load_mapping() -> Dict[str, Dict[str, str]]:
    """Load mapping JSON once and cache it."""
    if not MAPPING_PATH.exists():
        log_query.warning(f"⚠️ Speckle mapping file missing at {MAPPING_PATH}")
        return {}
    try:
        with MAPPING_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                log_query.error("Speckle mapping file is not a dict mapping")
                return {}
            return data
    except Exception as e:
        log_query.error(f"Failed to load Speckle mapping: {e}")
        return {}


def get_speckle_mapping(project_key: str) -> Optional[Dict[str, str]]:
    """Return Speckle mapping for a project key/name, if available."""
    key = _normalize_key(project_key)
    mapping = _load_mapping()
    hit = mapping.get(key)
    if hit:
        return {"project_key": key, **hit}
    # Secondary lookup: try case-insensitive match
    lowered = {k.lower(): k for k in mapping.keys()}
    if key.lower() in lowered:
        k = lowered[key.lower()]
        hit = mapping[k]
        return {"project_key": k, **hit}
    return None


def list_projects_with_speckle_models() -> List[Dict[str, str]]:
    """List all projects that have Speckle models in the mapping (unique by projectId/modelId)."""
    mapping = _load_mapping()
    seen = set()
    projects: List[Dict[str, str]] = []
    for key, meta in mapping.items():
        project_id = meta.get("projectId")
        model_id = meta.get("modelId")
        if not project_id or not model_id:
            continue
        dedup_key = (project_id, model_id)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        projects.append(
            {
                "project_key": key,
                "projectId": project_id,
                "modelId": model_id,
                "name": meta.get("name", key),
                "commitId": meta.get("commitId"),
            }
        )
    return projects
