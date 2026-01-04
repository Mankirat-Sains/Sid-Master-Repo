"""
Sidian Local Agent Package

This package provides the local agent that executes Excel operations
on behalf of the cloud orchestrator.

The local agent implements the Excel Tool API and maintains the critical
principle: Excel is the source of truth for all calculations.
"""

from .excel_tools import ExcelToolAPI, ExcelToolAPIError, execute_tool_sequence
from .semantic_loader import load_metadata, save_metadata, validate_metadata, SemanticMetadataError
from .config import load_config, AgentConfig
from .agent_service import LocalAgent

__all__ = [
    "ExcelToolAPI",
    "ExcelToolAPIError",
    "execute_tool_sequence",
    "load_metadata",
    "save_metadata",
    "validate_metadata",
    "SemanticMetadataError",
    "load_config",
    "AgentConfig",
    "LocalAgent"
]

__version__ = "0.1.0"

