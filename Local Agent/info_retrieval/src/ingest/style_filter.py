"""
Style exemplar quality filter.
Ensures only curated, high-quality templates enter the style index.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Optional, Set, Tuple


class StyleExemplarFilter:
    """
    Filters chunks to determine if they qualify as style exemplars.

    Criteria (any one may qualify):
    1. Explicit markers: Tagged as template/boilerplate/standard language.
    2. User curation: Manually pinned exemplar.
    3. Frequency: Appears in >= min_frequency documents with >= min_similarity (approximated).
    4. Quality score: > threshold for template-like sections.
    """

    def __init__(self, min_frequency: int = 3, min_similarity: float = 0.85, quality_threshold: float = 0.8) -> None:
        self.min_frequency = min_frequency
        self.min_similarity = min_similarity
        self.quality_threshold = quality_threshold
        self.chunk_frequency: Dict[Tuple[str, str], int] = defaultdict(int)
        self.pinned_chunks: Set[str] = set()

    def is_style_exemplar(self, chunk: str, metadata: Dict, quality_score: Optional[float] = None) -> bool:
        if not chunk or not chunk.strip():
            return False

        if self._is_marked_template(metadata):
            return True

        chunk_id = metadata.get("chunk_id")
        if chunk_id and chunk_id in self.pinned_chunks:
            return True

        persisted_freq = metadata.get("style_frequency")
        if isinstance(persisted_freq, int) and persisted_freq >= self.min_frequency:
            return True

        if self._is_frequent_pattern(chunk, metadata):
            return True

        if quality_score and quality_score >= self.quality_threshold and self._is_template_section(metadata):
            return True

        return False

    def _is_marked_template(self, metadata: Dict) -> bool:
        markers = ["template", "boilerplate", "standard language", "standard_text"]
        tags = metadata.get("tags", []) or []
        heading = str(metadata.get("heading", "")).lower()
        if any(marker in heading for marker in markers):
            return True
        if any(marker in str(tag).lower() for tag in tags for marker in markers):
            return True
        return False

    def _is_frequent_pattern(self, chunk: str, metadata: Dict) -> bool:
        section_type = metadata.get("section_type", "unknown")
        key = (self._normalize(chunk), section_type)
        self.chunk_frequency[key] += 1
        return self.chunk_frequency[key] >= self.min_frequency

    def _is_template_section(self, metadata: Dict) -> bool:
        template_sections = {
            "introduction",
            "assumptions",
            "limitations",
            "references",
            "conclusion",
            "executive_summary",
        }
        return metadata.get("section_type") in template_sections

    def _normalize(self, text: str) -> str:
        return " ".join(text.lower().split())

    def pin_exemplar(self, chunk_id: str) -> None:
        self.pinned_chunks.add(chunk_id)

    def compute_quality_score(self, chunk: str) -> float:
        score = 1.0
        word_count = len(chunk.split())
        if word_count < 10:
            score *= 0.5
        elif word_count > 500:
            score *= 0.7

        if not any(punct in chunk for punct in [".", "!", "?"]):
            score *= 0.6

        return score
