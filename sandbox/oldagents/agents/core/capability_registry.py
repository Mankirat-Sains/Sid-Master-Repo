"""
Capability Registry - Discovers and registers available tools, tables, and capabilities.

This ensures planning decisions are based on ACTUAL available resources, not hardcoded assumptions.
"""

import os
import inspect
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

# Try to import tools
try:
    from localagent.tools import ALL_TOOLS, SEARCH_TOOLS, ALL_CALCULATION_TOOLS
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False
    ALL_TOOLS = []
    SEARCH_TOOLS = []
    ALL_CALCULATION_TOOLS = []

# Try to check Supabase availability
try:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    HAS_SUPABASE_CONFIG = bool(SUPABASE_URL and SUPABASE_KEY)
except:
    HAS_SUPABASE_CONFIG = False

# Try to check if vector stores are actually initialized
try:
    from localagent.agents.search_orchestrator import (
        vs_smart, vs_large, vs_code, vs_coop,
        SUPA_SMART_TABLE, SUPA_LARGE_TABLE, SUPA_CODE_TABLE, SUPA_COOP_TABLE
    )
    HAS_VECTOR_STORES = True
except ImportError:
    HAS_VECTOR_STORES = False
    vs_smart = None
    vs_large = None
    vs_code = None
    vs_coop = None
    SUPA_SMART_TABLE = "smart_chunks"
    SUPA_LARGE_TABLE = "page_chunks"
    SUPA_CODE_TABLE = "code_chunks"
    SUPA_COOP_TABLE = "coop_chunks"


@dataclass
class ToolCapability:
    """Represents a single tool capability."""
    name: str
    description: str
    category: str  # "search", "calculation", "analysis", etc.
    function: callable = None
    docstring: str = ""


@dataclass
class TableCapability:
    """Represents a single database table/vector store."""
    name: str
    table_name: str
    description: str
    category: str  # "project_documents", "code", "coop_manual"
    available: bool = False
    vector_store: any = None


@dataclass
class CapabilityRegistry:
    """Registry of all available system capabilities."""
    
    # Tools
    search_tools: List[ToolCapability] = field(default_factory=list)
    calculation_tools: List[ToolCapability] = field(default_factory=list)
    all_tools: List[ToolCapability] = field(default_factory=list)
    
    # Vector stores / Tables
    vector_stores: List[TableCapability] = field(default_factory=list)
    
    # Availability flags
    has_supabase: bool = False
    has_project_db: bool = False
    has_code_db: bool = False
    has_coop_db: bool = False
    
    def __post_init__(self):
        """Discover capabilities on initialization."""
        self._discover_tools()
        self._discover_vector_stores()
    
    def _discover_tools(self):
        """Discover available tools from localagent.tools."""
        if not HAS_TOOLS:
            return
        
        # Discover search tools
        for tool in SEARCH_TOOLS:
            if callable(tool):
                doc = inspect.getdoc(tool) or ""
                self.search_tools.append(ToolCapability(
                    name=tool.__name__,
                    description=doc.split('\n')[0] if doc else f"Tool: {tool.__name__}",
                    category="search",
                    function=tool,
                    docstring=doc
                ))
        
        # Discover calculation tools
        for tool in ALL_CALCULATION_TOOLS:
            if callable(tool):
                doc = inspect.getdoc(tool) or ""
                self.calculation_tools.append(ToolCapability(
                    name=tool.__name__,
                    description=doc.split('\n')[0] if doc else f"Tool: {tool.__name__}",
                    category="calculation",
                    function=tool,
                    docstring=doc
                ))
        
        # Combine all tools
        self.all_tools = self.search_tools + self.calculation_tools
    
    def _discover_vector_stores(self):
        """Discover available vector stores/tables."""
        self.has_supabase = HAS_SUPABASE_CONFIG
        
        # Check project database tables
        if HAS_VECTOR_STORES:
            # Smart chunks (project documents - detailed)
            self.vector_stores.append(TableCapability(
                name="smart_chunks",
                table_name=SUPA_SMART_TABLE,
                description="Project documents with detailed features and specifications",
                category="project_documents",
                available=vs_smart is not None,
                vector_store=vs_smart
            ))
            self.has_project_db = vs_smart is not None
            
            # Large chunks (project documents - full pages)
            self.vector_stores.append(TableCapability(
                name="page_chunks",
                table_name=SUPA_LARGE_TABLE,
                description="Full page documents from projects",
                category="project_documents",
                available=vs_large is not None,
                vector_store=vs_large
            ))
            
            # Code chunks (building codes and standards)
            self.vector_stores.append(TableCapability(
                name="code_chunks",
                table_name=SUPA_CODE_TABLE,
                description="Building codes, standards, and technical references",
                category="code",
                available=vs_code is not None,
                vector_store=vs_code
            ))
            self.has_code_db = vs_code is not None
            
            # Coop chunks (company processes and training)
            self.vector_stores.append(TableCapability(
                name="coop_chunks",
                table_name=SUPA_COOP_TABLE,
                description="Company processes, training manuals, and internal documentation",
                category="coop_manual",
                available=vs_coop is not None,
                vector_store=vs_coop
            ))
            self.has_coop_db = vs_coop is not None
        else:
            # If we can't import, check config at least
            if HAS_SUPABASE_CONFIG:
                # Assume tables might be available if Supabase is configured
                self.vector_stores.append(TableCapability(
                    name="smart_chunks",
                    table_name=SUPA_SMART_TABLE,
                    description="Project documents with detailed features",
                    category="project_documents",
                    available=True  # Optimistic - will fail gracefully if not
                ))
                self.has_project_db = True
    
    def get_available_data_sources(self) -> List[str]:
        """Get list of available data sources for planning."""
        sources = []
        
        if self.has_project_db:
            sources.append("rag_documents")  # Project documents via RAG
        
        if self.has_code_db:
            sources.append("rag_codes")  # Building codes via RAG
        
        if self.has_coop_db:
            sources.append("rag_internal_docs")  # Internal docs via RAG
        
        # Note: supabase_metadata and graphql_speckle are separate systems
        # They should be checked separately if needed
        
        return sources
    
    def get_available_tools_summary(self) -> str:
        """Get human-readable summary of available tools."""
        if not self.all_tools:
            return "No tools available"
        
        summary = []
        if self.search_tools:
            summary.append(f"**Search Tools ({len(self.search_tools)}):**")
            for tool in self.search_tools:
                summary.append(f"  - `{tool.name}`: {tool.description}")
        
        if self.calculation_tools:
            summary.append(f"\n**Calculation Tools ({len(self.calculation_tools)}):**")
            for tool in self.calculation_tools:
                summary.append(f"  - `{tool.name}`: {tool.description}")
        
        return "\n".join(summary)
    
    def get_available_tables_summary(self) -> str:
        """Get human-readable summary of available tables."""
        available_tables = [vs for vs in self.vector_stores if vs.available]
        
        if not available_tables:
            return "No vector stores available"
        
        summary = []
        summary.append(f"**Available Tables ({len(available_tables)}):**")
        for table in available_tables:
            status = "✅" if table.available else "❌"
            summary.append(f"  {status} `{table.table_name}` ({table.category}): {table.description}")
        
        return "\n".join(summary)
    
    def to_planning_context(self) -> str:
        """Convert registry to context string for LLM planning."""
        context_parts = []
        
        # Available data sources
        data_sources = self.get_available_data_sources()
        if data_sources:
            context_parts.append(f"**Available Data Sources:** {', '.join(data_sources)}")
        else:
            context_parts.append("**Available Data Sources:** None (no vector stores configured)")
        
        # Available tables
        available_tables = [vs for vs in self.vector_stores if vs.available]
        if available_tables:
            table_names = [vs.table_name for vs in available_tables]
            context_parts.append(f"**Available Tables:** {', '.join(table_names)}")
        
        # Available tools
        if self.all_tools:
            tool_names = [tool.name for tool in self.all_tools]
            context_parts.append(f"**Available Tools:** {', '.join(tool_names)}")
        
        return "\n".join(context_parts)


# Global registry instance
_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    """Get or create the global capability registry."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


def refresh_registry():
    """Refresh the capability registry (useful after configuration changes)."""
    global _registry
    _registry = CapabilityRegistry()
    return _registry




