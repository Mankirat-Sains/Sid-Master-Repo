"""
Intelligent Excel Parser Package

This package provides AI-driven parsing of Excel workbooks to create
semantic metadata for the local agent.

Key Features:
- Legend detection using AI (no hardcoding)
- Cell classification by color
- Semantic understanding from context
- Intelligent grouping of related parameters
"""

from .intelligent_excel_parser import IntelligentExcelParser
from .metadata_converter import (
    convert_to_local_agent_format,
    convert_parser_output_to_metadata
)

__all__ = [
    "IntelligentExcelParser",
    "convert_to_local_agent_format",
    "convert_parser_output_to_metadata"
]

__version__ = "0.1.0"

