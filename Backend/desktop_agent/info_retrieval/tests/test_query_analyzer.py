import pytest

from tier2.query_analyzer import QueryAnalyzer


def test_analyze_methodology_request() -> None:
    """Test parsing methodology request."""
    analyzer = QueryAnalyzer()

    result = analyzer.analyze("Draft methodology section for structural beam design per ACI 318-19")

    assert result["doc_type"] == "design_report"
    assert result["section_type"] == "methodology"
    assert result["engineering_function"] == "describe_section"
    assert result["constraints"]["calculation_type"] == "structural"
    assert "ACI 318-19" in result["constraints"]["code_references"]
    assert result["constraints"]["element_type"] == "beam"


def test_analyze_assumptions_request() -> None:
    """Test parsing assumptions request."""
    analyzer = QueryAnalyzer()

    result = analyzer.analyze("Write assumptions for thermal HVAC analysis")

    assert result["section_type"] == "assumptions"
    assert result["constraints"]["calculation_type"] == "thermal"
    assert result["constraints"]["system_type"] == "HVAC"
