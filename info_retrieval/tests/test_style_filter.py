import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ingest.style_filter import StyleExemplarFilter  # noqa: E402


def test_marked_template_passes():
    filt = StyleExemplarFilter()
    chunk = "Standard assumptions for structural design..."
    metadata = {"tags": ["template"], "section_type": "assumptions"}
    assert filt.is_style_exemplar(chunk, metadata) is True


def test_low_quality_rejected():
    filt = StyleExemplarFilter()
    chunk = "short"
    metadata = {"section_type": "introduction"}
    quality = filt.compute_quality_score(chunk)
    assert filt.is_style_exemplar(chunk, metadata, quality) is False


def test_high_quality_intro_passes():
    filt = StyleExemplarFilter()
    chunk = (
        "This calculation report presents the structural analysis of the foundation system. "
        "The analysis follows ACI 318-19 and considers load combinations per ASCE 7-22."
    )
    metadata = {"section_type": "introduction"}
    quality = filt.compute_quality_score(chunk)
    assert quality > 0.7
    assert filt.is_style_exemplar(chunk, metadata, quality) is True
