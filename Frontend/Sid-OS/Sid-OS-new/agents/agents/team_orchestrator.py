"""
Team Orchestrator - top-level orchestrator that routes to specialized agents.
Fast routing: "This is a search task" → delegates to SearchOrchestrator
This is faster than having one orchestrator handle everything.

Now includes strategic planning:
- Intent classification (project_search, design_guidance, process_knowledge, etc.)
- Data source routing (which systems to query)
- Strategy selection (metadata_first, code_first, process_only, etc.)
"""

import os
import json
from typing import Dict, List, Optional, Callable
from openai import OpenAI
from .base_agent import BaseAgent, AgentState

# Import capability registry to discover available tools and tables
try:
    from localagent.core.capability_registry import get_registry
    HAS_CAPABILITY_REGISTRY = True
except ImportError:
    HAS_CAPABILITY_REGISTRY = False
    def get_registry():
        return None


class TeamOrchestrator(BaseAgent):
    """
    Top-level orchestrator that routes tasks to specialized agents.
    
    This is FAST because it:
    1. Only does high-level routing (search, analysis, etc.)
    2. Delegates granular planning to specialized orchestrators
    3. No detailed reasoning overhead
    
    Architecture:
    - TeamOrchestrator (this): Routes to specialized agents
    - SearchOrchestrator: Handles search tasks
    - DocumentOrchestrator: Handles document analysis (future)
    - etc.
    """
    
    def __init__(self, api_key: Optional[str] = None, specialized_agents: Dict = None):
        super().__init__(name="team_orchestrator")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.specialized_agents = specialized_agents or {}
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
            except Exception:
                self.enabled = False
        else:
            self.enabled = False
    
    def plan_execution(self, user_query: str) -> Dict:
        """
        Strategic planning - determines WHAT to do, not HOW.
        
        This does:
        1. Intent classification (project_search, design_guidance, process_knowledge, etc.)
        2. Data source routing (which systems to query) - BASED ON ACTUAL AVAILABLE CAPABILITIES
        3. Strategy selection (metadata_first, code_first, process_only, etc.)
        
        Returns:
            Dict with:
            - intent: Query intent type
            - data_sources: List of data sources to query (filtered to available ones)
            - strategy: Execution strategy
            - reasoning: Why this approach
            - expected_steps: High-level steps
            - planning_intelligence: Detailed planning info for logging
        """
        # Get available capabilities
        registry = None
        capability_context = ""
        available_data_sources = []
        
        if HAS_CAPABILITY_REGISTRY:
            try:
                registry = get_registry()
                if registry:
                    available_data_sources = registry.get_available_data_sources()
                    capability_context = registry.to_planning_context()
            except Exception as e:
                # If registry fails, continue without it
                pass
        
        if not self.enabled:
            # Fallback planning - use only available data sources
            query_lower = user_query.lower()
            
            # Filter to available sources
            fallback_sources = available_data_sources if available_data_sources else ["rag_documents"]
            
            if any(word in query_lower for word in ["find", "search", "project"]):
                # Only include sources that are actually available
                filtered_sources = [s for s in ["rag_documents"] if s in fallback_sources]
                return {
                    "intent": "project_search",
                    "data_sources": filtered_sources if filtered_sources else fallback_sources,
                    "strategy": "metadata_first",
                    "reasoning": "User wants to find projects - will query metadata then documents",
                    "expected_steps": ["Extract search criteria", "Query metadata", "Search documents", "Return results"],
                    "planning_intelligence": {"intent_classification": "project_search", "confidence": 0.8}
                }
            elif any(word in query_lower for word in ["design", "how to"]):
                # Only include sources that are actually available
                filtered_sources = [s for s in ["rag_codes", "calculation_tools"] if s in fallback_sources or s == "calculation_tools"]
                return {
                    "intent": "design_guidance",
                    "data_sources": filtered_sources if filtered_sources else fallback_sources,
                    "strategy": "code_first",
                    "reasoning": "User wants design guidance - will search codes then use calculations",
                    "expected_steps": ["Search building codes", "Extract parameters", "Run calculations", "Synthesize"],
                    "planning_intelligence": {"intent_classification": "design_guidance", "confidence": 0.8}
                }
            return {
                "intent": "general",
                "data_sources": fallback_sources,
                "strategy": "document_first",
                "reasoning": "General query - will search documents",
                "expected_steps": ["Search documents", "Synthesize results"],
                "planning_intelligence": {"intent_classification": "general", "confidence": 0.5}
            }
        
        # Build system prompt with ACTUAL available capabilities
        system_prompt = """You are a strategic planning agent. Analyze user queries and determine:
1. INTENT: What type of query is this?
   - project_search: Finding specific projects (e.g., "find me a project with 50x100")
   - design_guidance: How to design something (e.g., "how to design a beam")
   - process_knowledge: Company-specific processes (e.g., "how we do truss design")
   - technical_question: General engineering questions

2. DATA SOURCES: Which systems should be queried?
   IMPORTANT: Only select from AVAILABLE data sources listed below. Do NOT select sources that are not available.
   
   Available data sources:
   - rag_documents: Project documents, technical drawings (via RAG) - ONLY if project_db is available
   - rag_codes: Building codes, standards (via RAG) - ONLY if code_db is available
   - rag_internal_docs: Company processes, training manuals (via RAG) - ONLY if coop_db is available
   - calculation_tools: Structural analysis, section properties - Always available
   
   Note: supabase_metadata and graphql_speckle are separate systems and may not be available.

3. STRATEGY: How should we execute?
   - metadata_first: Query structured metadata first, then documents
   - document_first: Search documents first, extract metadata
   - code_first: Search codes first, extract parameters, then calculate
   - process_only: Search internal docs only
   - hybrid: Multiple sources in parallel

CRITICAL: Only select data sources that are ACTUALLY AVAILABLE. If a data source is not available, do not include it in your response.

Respond with JSON:
{
  "intent": "...",
  "data_sources": ["source1", "source2"],  // ONLY from available sources above
  "strategy": "...",
  "reasoning": "Why this approach",
  "expected_steps": ["step1", "step2", ...]
}"""
        
        # Add capability context if available
        if capability_context:
            system_prompt += f"\n\nCURRENT SYSTEM CAPABILITIES:\n{capability_context}"
        
        # Strategic planning with LLM
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        try:
            plan = json.loads(response.choices[0].message.content)
            
            # FILTER data sources to only include what's actually available
            requested_sources = plan.get("data_sources", [])
            if available_data_sources:
                # Filter to only available sources
                filtered_sources = [
                    src for src in requested_sources 
                    if src in available_data_sources or src == "calculation_tools"
                ]
                # If LLM selected unavailable sources, replace with available ones
                if filtered_sources != requested_sources:
                    plan["data_sources"] = filtered_sources
                    plan["reasoning"] += f" (Note: Filtered to available sources: {', '.join(filtered_sources)})"
            else:
                # If no registry, at least ensure we don't select non-existent sources
                # Keep only safe defaults
                safe_sources = [s for s in requested_sources if s in ["rag_documents", "rag_codes", "rag_internal_docs", "calculation_tools"]]
                if safe_sources:
                    plan["data_sources"] = safe_sources
            
            # Add planning intelligence for logging
            plan["planning_intelligence"] = {
                "intent_classification": plan.get("intent", "unknown"),
                "data_source_count": len(plan.get("data_sources", [])),
                "strategy": plan.get("strategy", "unknown"),
                "confidence": 0.9,  # High confidence for LLM-based planning
                "available_sources": available_data_sources if available_data_sources else []
            }
            
            return plan
        except Exception as e:
            # Fallback planning
            return {
                "intent": "general",
                "data_sources": ["rag_documents"],
                "strategy": "document_first",
                "reasoning": f"Planning failed: {str(e)}",
                "expected_steps": ["Search documents"],
                "planning_intelligence": {"intent_classification": "general", "confidence": 0.3}
            }
    
    def route_task(self, user_query: str) -> Dict:
        """
        Fast routing: determine which specialized agent should handle this.
        
        Returns:
            Dict with:
            - agent_type: "search", "document", "analysis", etc.
            - confidence: How confident we are in this routing
            - reasoning: Brief explanation
        """
        if not self.enabled:
            # Simple keyword-based routing fallback
            query_lower = user_query.lower()
            if any(word in query_lower for word in ["find", "search", "project", "past", "similar", "design", "how"]):
                return {"agent_type": "search", "confidence": 0.8, "reasoning": "Contains search/design keywords"}
            return {"agent_type": "general", "confidence": 0.5, "reasoning": "Default routing"}
        
        # Fast LLM routing - minimal prompt for speed
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a fast task router. Classify queries into agent types:
- search: Finding projects, searching databases, retrieving information, design questions
- document: Analyzing documents, reading files, understanding content
- analysis: Complex analysis, synthesis, recommendations
- general: Other tasks

Respond with JSON: {"agent_type": "...", "confidence": 0.0-1.0, "reasoning": "..."}"""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {"agent_type": "general", "confidence": 0.5, "reasoning": "Routing failed"}
    
    def execute(self, task: str, context: Dict = None) -> Dict:
        """
        Execute by routing to specialized agent with strategic planning.
        
        Args:
            task: User query
            context: Additional context (can include session_id, data_sources, etc.)
            
        Returns:
            Dict with execution results from specialized agent, including:
            - results: Final answer
            - trace: Execution trace with thinking_log
            - plan: Planning information
            - routing: Routing information
            - planning: Strategic planning information
        """
        context = context or {}
        
        # Initialize state
        self.state = AgentState(
            task=task,
            context=context,
            completed_steps=[],
            results={}
        )
        
        # Strategic planning - determines WHAT to do (based on actual capabilities)
        planning = self.plan_execution(task)
        
        # Fast routing - determines WHICH agent
        routing = self.route_task(task)
        agent_type = routing.get("agent_type", "general")
        
        # Generate high-level plan display (like retrieve_db_info.plan.md)
        high_level_plan = self._generate_high_level_plan(planning, routing, task)
        
        # Add planning info to context for specialized agent
        context_with_planning = {
            **context,
            "planning": planning,
            "routing": routing
        }
        
        # Get specialized agent
        specialized_agent = self.specialized_agents.get(agent_type)
        
        if not specialized_agent:
            return {
                "error": f"No specialized agent available for type: {agent_type}",
                "routing": routing,
                "planning": planning,
                "success": False
            }
        
        # Delegate to specialized agent with planning context
        result = specialized_agent.execute(task, context_with_planning)
        
        # Add planning and routing info to result
        result["routing"] = routing
        result["planning"] = planning
        result["orchestrator"] = "team_orchestrator"
        result["specialized_agent"] = agent_type
        result["high_level_plan"] = high_level_plan  # Add high-level plan for display
        
        return result
    
    def _generate_high_level_plan(self, planning: Dict, routing: Dict, task: str) -> str:
        """
        Generate a high-level execution plan (like retrieve_db_info.plan.md format).
        
        This shows the user what steps will be taken, similar to Cursor's planning display.
        """
        intent = planning.get("intent", "general")
        expected_steps = planning.get("expected_steps", [])
        strategy = planning.get("strategy", "unknown")
        data_sources = planning.get("data_sources", [])
        reasoning = planning.get("reasoning", "")
        
        # Build numbered plan
        plan_lines = [
            "## 🎯 Execution Plan",
            "",
            f"**Query:** \"{task}\"",
            "",
            "**High-Level Steps:**"
        ]
        
        # Add numbered steps
        for i, step in enumerate(expected_steps, 1):
            plan_lines.append(f"{i}. {step}")
        
        # Add metadata
        plan_lines.extend([
            "",
            f"**Selected Orchestrator:** {routing.get('agent_type', 'unknown').title()}Orchestrator",
            f"**Confidence:** {routing.get('confidence', 0.0):.2f}",
            f"**Strategy:** {strategy}",
            f"**Data Sources:** {', '.join(data_sources) if data_sources else 'None'}",
            "",
            f"**Reasoning:** {reasoning}"
        ])
        
        return "\n".join(plan_lines)

