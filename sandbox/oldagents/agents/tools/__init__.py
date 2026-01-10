"""
Tools module - Python functions that represent system capabilities.
LLM will choose which tools to call based on user queries.
"""

from .search_tools import ALL_TOOLS as SEARCH_TOOLS
from .calculation_tools import ALL_CALCULATION_TOOLS

# Combine all tools
ALL_TOOLS = SEARCH_TOOLS + ALL_CALCULATION_TOOLS

__all__ = [
    'ALL_TOOLS',
    'SEARCH_TOOLS',
    'ALL_CALCULATION_TOOLS'
]
