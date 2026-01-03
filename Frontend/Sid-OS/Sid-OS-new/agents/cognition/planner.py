"""
Planner - core planning algorithm used by all agents.
Generates human-readable plans before execution using MD file examples as reference.
This is the central planning component that all specialized agents build upon.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from openai import OpenAI


class Planner:
    """
    Core planning algorithm - generates plans using MD file examples as reference.
    All agents use this for consistent, example-guided planning.
    """
    
    def __init__(self, api_key: Optional[str] = None, core_path: Optional[Path] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.core_path = core_path or Path(__file__).parent.parent / "core"
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
            except Exception as e:
                print(f"⚠ Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            self.enabled = False
        
        # Load MD file examples for reference
        self._load_md_examples()
    
    def _load_md_examples(self):
        """Load MD file examples to use as reference in prompts."""
        self.examples = {
            "execution_graphs": {},
            "plans": {}
        }
        
        # Load execution graphs
        graphs_path = self.core_path / "execution_graphs"
        if graphs_path.exists():
            for graph_file in graphs_path.glob("*.graph.md"):
                try:
                    content = graph_file.read_text()
                    self.examples["execution_graphs"][graph_file.stem] = content
                except Exception:
                    pass
        
        # Load plans
        plans_path = self.core_path / "plans"
        if plans_path.exists():
            for plan_file in plans_path.glob("*.plan.md"):
                try:
                    content = plan_file.read_text()
                    self.examples["plans"][plan_file.stem] = content
                except Exception:
                    pass
    
    def _get_relevant_examples(self, domain: str = None) -> str:
        """
        Get relevant MD file examples based on domain.
        Returns formatted examples to include in prompts.
        """
        examples_text = ""
        
        # Find relevant examples based on domain
        if domain == "search" or domain == "find_past_project":
            # Use retrieve_db_info examples
            if "retrieve_db_info" in self.examples["execution_graphs"]:
                examples_text += "\n\n**Reference Execution Graph (from MD files):**\n"
                examples_text += "```\n"
                examples_text += self.examples["execution_graphs"]["retrieve_db_info"]
                examples_text += "\n```\n"
            
            if "retrieve_db_info" in self.examples["plans"]:
                examples_text += "\n\n**Reference Plan (from MD files):**\n"
                examples_text += "```\n"
                examples_text += self.examples["plans"]["retrieve_db_info"]
                examples_text += "\n```\n"
        
        elif domain == "document" or domain == "rfp_response":
            # Use written_work_analysis examples
            if "written_work_analysis" in self.examples["execution_graphs"]:
                examples_text += "\n\n**Reference Execution Graph (from MD files):**\n"
                examples_text += "```\n"
                examples_text += self.examples["execution_graphs"]["written_work_analysis"]
                examples_text += "\n```\n"
            
            if "written_work_improvement" in self.examples["plans"]:
                examples_text += "\n\n**Reference Plan (from MD files):**\n"
                examples_text += "```\n"
                examples_text += self.examples["plans"]["written_work_improvement"]
                examples_text += "\n```\n"
        
        # If no domain-specific examples, include general examples
        if not examples_text and self.examples["execution_graphs"]:
            first_graph = list(self.examples["execution_graphs"].values())[0]
            examples_text += "\n\n**Reference Execution Graph (from MD files):**\n"
            examples_text += "```\n"
            examples_text += first_graph
            examples_text += "\n```\n"
        
        return examples_text
    
    def generate_plan(
        self, 
        user_query: str, 
        available_tools: List[Callable],
        domain: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Core planning algorithm - generates plans using MD file examples as reference.
        All agents should use this method for consistent planning.
        
        Args:
            user_query: The user's query
            available_tools: List of available tool functions
            domain: Optional domain hint (e.g., "search", "document") for example selection
            context: Optional additional context (e.g., data sources, constraints)
            
        Returns:
            Dict with:
            - plan: List of human-readable steps (what will be done)
            - reasoning: Explanation of why this approach
            - tools_needed: List of tools that will likely be used
            - estimated_steps: Number of steps expected
            - data_sources: Data sources to use (if applicable)
            - strategy: Strategy/approach (if applicable)
        """
        if not self.enabled:
            return {
                "plan": ["AI planning not available. Set OPENAI_API_KEY to enable."],
                "reasoning": "Planning requires AI. Falling back to basic execution.",
                "tools_needed": [],
                "estimated_steps": 0
            }
        
        # Get tool names and descriptions
        tool_names = [tool.__name__ for tool in available_tools]
        tool_descriptions = "\n".join([
            f"- {tool.__name__}: {tool.__doc__.split(chr(10))[0] if tool.__doc__ else 'No description'}"
            for tool in available_tools
        ])
        
        # Get relevant MD file examples
        md_examples = self._get_relevant_examples(domain)
        
        # Build context information
        context_info = ""
        if context:
            if context.get("data_sources"):
                context_info += f"\nData Sources: {', '.join(context['data_sources'])}\n"
            if context.get("execution_mode"):
                context_info += f"Execution Mode: {context['execution_mode']}\n"
        
        # Ask LLM to generate a plan with MD examples as reference
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a planning agent that creates clear, step-by-step plans for answering user queries.

Your job is to:
1. Understand what the user wants
2. Reference the MD file examples below to understand proven patterns
3. Create a human-readable plan showing the steps
4. Explain your reasoning
5. Identify which tools will be needed

{md_examples}

Use the reference examples above as guidance for:
- What steps to take
- How to structure the workflow
- What inputs/outputs to expect
- When to branch or request clarification

Format your response as JSON with:
- plan: array of step descriptions (what will be done)
- reasoning: explanation of why this approach
- tools_needed: array of tool names that will be used
- estimated_steps: number of steps
- data_sources: array of data sources (if applicable)
- strategy: strategy/approach name (if applicable)

Be specific and clear. Each step should be actionable. Follow patterns from the reference examples."""
                },
                {
                    "role": "user",
                    "content": f"""User Query: "{user_query}"

Available Tools:
{tool_descriptions}
{context_info}

Generate a plan to answer this query. Reference the MD examples above for proven patterns.
Show:
1. What steps will be taken (plan)
2. Why this approach (reasoning)
3. Which tools will be used (tools_needed)

Return ONLY valid JSON, no markdown."""
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            plan_data = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields exist
            return {
                "plan": plan_data.get("plan", []),
                "reasoning": plan_data.get("reasoning", "No reasoning provided"),
                "tools_needed": plan_data.get("tools_needed", []),
                "estimated_steps": plan_data.get("estimated_steps", len(plan_data.get("plan", []))),
                "data_sources": plan_data.get("data_sources", []),
                "strategy": plan_data.get("strategy", "")
            }
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            content = response.choices[0].message.content
            return {
                "plan": [content] if content else ["Failed to generate plan"],
                "reasoning": "Plan generation succeeded but formatting failed",
                "tools_needed": [],
                "estimated_steps": 0
            }
    
    def explain_thinking(self, user_query: str, plan: Dict) -> str:
        """
        Generate a natural language explanation of the thinking process.
        This is what gets shown to humans in logs/UI.
        """
        if not self.enabled:
            return "AI explanation not available."
        
        plan_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan.get("plan", []))])
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You explain technical plans in clear, conversational language. Show the thinking process."
                },
                {
                    "role": "user",
                    "content": f"""User asked: "{user_query}"

Plan:
{plan_steps}

Reasoning: {plan.get('reasoning', '')}

Explain the thinking process in 2-3 sentences. Why are we taking these steps? What's the strategy?"""
                }
            ],
            temperature=0.5
        )
        
        return response.choices[0].message.content.strip()

