"""DesktopAgent Nodes - Desktop application integration"""

from .desktop_router import node_desktop_router
from .ExcelAgent.excel_agent import node_excel_agent
from .WordAgent.word_agent import node_word_agent
from .RevitAgent.revit_agent import node_revit_agent

__all__ = [
    "node_desktop_router",
    "node_excel_agent",
    "node_word_agent",
    "node_revit_agent",
]


