"""WordAgent Nodes - Word-specific desktop agent functionality"""

from .word_agent import node_word_agent
from .plan import node_doc_plan
from .think import node_doc_think
from .act import node_doc_act
from .executor import node_desktop_execute
from .section_generator import node_doc_generate_section, SectionGenerator
from .report_generator import node_doc_generate_report
from .answer_adapter import node_doc_answer_adapter
from .task_classifier import node_doc_task_classifier
from .deep_desktop_loop import node_deep_desktop_loop

# Tools
from .tools import get_docgen_tool, DocGenTool, get_doc_edit_tool, DocEditTool

__all__ = [
    "node_word_agent",
    "node_doc_plan",
    "node_doc_think",
    "node_doc_act",
    "node_desktop_execute",
    "node_doc_generate_section",
    "node_doc_generate_report",
    "node_doc_answer_adapter",
    "node_doc_task_classifier",
    "node_deep_desktop_loop",
    "SectionGenerator",
    "get_docgen_tool",
    "DocGenTool",
    "get_doc_edit_tool",
    "DocEditTool",
]
