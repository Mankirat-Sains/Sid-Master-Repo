"""
Demo cache loader and lookup utilities.

This is intentionally lightweight and only used for demo fast-path responses.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _normalize_query(query: str) -> str:
    """Normalize a query for matching: lowercase, trim, and collapse whitespace."""
    return " ".join((query or "").strip().lower().split())


@dataclass
class DemoCacheEntry:
    key: str
    aliases: List[str]
    payload: Dict


class DemoCache:
    """In-memory demo cache with normalized lookup."""

    def __init__(self, entries: List[DemoCacheEntry]):
        self._lookup: Dict[str, Tuple[str, Dict]] = {}
        for entry in entries:
            normalized_key = _normalize_query(entry.key)
            self._lookup[normalized_key] = (entry.key, entry.payload)
            for alias in entry.aliases or []:
                norm_alias = _normalize_query(alias)
                self._lookup[norm_alias] = (entry.key, entry.payload)

    def lookup(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Lookup a query in the demo cache.

        Returns:
            payload dict (or None), matched canonical key (or None)
        """
        normalized = _normalize_query(query)
        hit = self._lookup.get(normalized)
        if not hit:
            return None, None
        canonical_key, payload = hit
        return payload, canonical_key


def load_demo_cache(path: Optional[Path] = None) -> Optional[DemoCache]:
    """
    Load demo cache from JSON file.

    The JSON structure:
    [
      {
        "key": "pull up the 2025 document",
        "aliases": ["pull up the 2025 doc", "show the 2025 document"],
        "answer_markdown": "...",
        "citations": [],
        "artifacts": [],
        "confidence": 0.99
      }
    ]
    """
    try:
        cache_path = path or Path(__file__).parent / "demo_cache.json"
        with cache_path.open("r", encoding="utf-8") as f:
            raw_entries = json.load(f)

        entries: List[DemoCacheEntry] = []
        for item in raw_entries:
            # Ensure defaults even if fields are missing
            payload = {
                "answer_markdown": item.get("answer_markdown", ""),
                "citations": item.get("citations", []),
                "artifacts": item.get("artifacts", []),
                "confidence": item.get("confidence", 0.0),
            }
            entries.append(
                DemoCacheEntry(
                    key=item.get("key", ""),
                    aliases=item.get("aliases", []) or [],
                    payload=payload,
                )
            )

        if not entries:
            logger.warning("Demo cache loaded but empty.")
        else:
            logger.info("Demo cache loaded with %d entries.", len(entries))

        return DemoCache(entries)
    except FileNotFoundError:
        logger.warning("Demo cache file not found at %s", path or Path(__file__).parent / "demo_cache.json")
    except Exception as e:
        logger.error("Failed to load demo cache: %s", e)
    return None
