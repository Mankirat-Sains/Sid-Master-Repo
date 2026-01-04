"""
Multi-agent entry point - uses TeamOrchestrator for fast routing.
This is faster than single orchestrator because it routes to specialized agents.
"""

import os
import sys
from pathlib import Path
from typing import Dict

# Check if LangGraph is available
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

# Try to load .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Import agents and tools
from agents.team_orchestrator import TeamOrchestrator
from agents.search_orchestrator import SearchOrchestrator
from tools import ALL_TOOLS


def print_routing(routing: Dict):
    """Print routing decision."""
    print("\n" + "=" * 60)
    print("ROUTING")
    print("=" * 60)
    print(f"Agent Type: {routing.get('agent_type', 'unknown')}")
    print(f"Confidence: {routing.get('confidence', 0):.2f}")
    print(f"Reasoning: {routing.get('reasoning', 'No reasoning')}")


def print_plan(plan: Dict):
    """Print the plan with clear thinking process."""
    if not plan:
        return
    
    print("\n" + "=" * 60)
    print("PLAN & THINKING")
    print("=" * 60)
    
    # Show thinking first (most important)
    if plan.get("thinking"):
        print("\n🧠 SYSTEM THINKING:")
        print("-" * 60)
        # Split thinking into lines if it's a long string
        thinking = plan['thinking']
        if isinstance(thinking, str):
            # Remove duplicate lines (sometimes thinking gets duplicated)
            lines = thinking.split('\n')
            seen = set()
            unique_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen:
                    seen.add(line_stripped)
                    unique_lines.append(line)
            for line in unique_lines:
                if line.strip():  # Only print non-empty lines
                    print(f"  {line.strip()}")
        else:
            print(f"  {thinking}")
    
    if plan.get("reasoning"):
        print("\n💭 REASONING:")
        print("-" * 60)
        reasoning = plan['reasoning']
        if isinstance(reasoning, str):
            # Remove duplicate lines
            lines = reasoning.split('\n')
            seen = set()
            unique_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen:
                    seen.add(line_stripped)
                    unique_lines.append(line)
            for line in unique_lines:
                if line.strip():  # Only print non-empty lines
                    print(f"  {line.strip()}")
        else:
            print(f"  {reasoning}")
    
    # Support both "plan" and "steps" keys for backward compatibility
    steps = plan.get("steps") or plan.get("plan", [])
    if steps:
        print("\n📋 EXECUTION STEPS:")
        print("-" * 60)
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
    
    if plan.get("data_sources"):
        print(f"\n📊 Data Sources: {', '.join(plan['data_sources'])}")
    
    if plan.get("search_strategy") or plan.get("strategy"):
        strategy = plan.get("search_strategy") or plan.get("strategy", "")
        print(f"🎯 Strategy: {strategy}")
    
    if plan.get("tools_needed"):
        print(f"\n🔧 Tools Needed:")
        for tool in plan["tools_needed"]:
            print(f"  - {tool}")


def print_execution_trace(result: Dict):
    """Print execution trace with full transparency."""
    print("\n" + "=" * 60)
    print("EXECUTION TRACE")
    print("=" * 60)
    
    # Use structured trace if available
    trace = result.get("trace")
    if trace:
        # Print thinking log prominently
        if trace.thinking_log:
            print("\n🧠 SYSTEM THINKING LOG:")
            print("-" * 60)
            # Remove duplicate thoughts
            seen = set()
            for thought in trace.thinking_log:
                thought_stripped = thought.strip()
                if thought_stripped and thought_stripped not in seen:
                    seen.add(thought_stripped)
                    # Truncate if too long
                    if len(thought_stripped) > 150:
                        print(f"  • {thought_stripped[:147]}...")
                    else:
                        print(f"  • {thought_stripped}")
        
        # Print steps with full detail
        if trace.steps:
            print("\n⚙️ EXECUTION STEPS:")
            print("-" * 60)
            for step in trace.steps:
                status_icon = {
                    "completed": "✓",
                    "error": "✗",
                    "blocked": "⊘",
                    "skipped": "⊘",
                    "running": "⟳",
                    "pending": "○"
                }.get(step.status.value, "?")
                
                print(f"\n{status_icon} STEP {step.step_number}: {step.tool_name} ({step.location})")
                
                if step.thinking:
                    print(f"   💭 {step.thinking}")
                
                if step.inputs:
                    print(f"   📥 Inputs:")
                    for key, value in step.inputs.items():
                        display_value = str(value)
                        if len(display_value) > 100:
                            display_value = display_value[:97] + "..."
                        print(f"      • {key}: {display_value}")
                
                if step.outputs:
                    print(f"   📤 Outputs:")
                    for key, value in step.outputs.items():
                        display_value = str(value)
                        if len(display_value) > 100:
                            display_value = display_value[:97] + "..."
                        print(f"      • {key}: {display_value}")
                
                if step.branch_taken:
                    print(f"   🔀 Branch Taken: → {step.branch_taken}")
                
                if step.duration_ms:
                    print(f"   ⏱️  Duration: {step.duration_ms}ms")
                
                if step.error:
                    print(f"   ❌ Error: {step.error}")
        
        # Print available outputs (data flow)
        if trace.available_outputs:
            print("\n" + "-" * 60)
            print("Available Outputs (Data Flow):")
            for key, value in trace.available_outputs.items():
                display_value = str(value)
                if len(display_value) > 80:
                    display_value = display_value[:77] + "..."
                print(f"  - {key}: {display_value}")
        
        # Print final status
        print("\n" + "-" * 60)
        print(f"Final Status: {trace.final_status.value}")
        
        if trace.errors:
            print("\nErrors:")
            for error in trace.errors:
                print(f"  ✗ {error}")
    
    # Fallback to old format if no trace
    elif result.get("steps"):
        print("\nSteps (legacy format):")
        for i, step in enumerate(result["steps"], 1):
            print(f"\n--- STEP {i}: {step.get('tool', 'unknown')} ---")
            print(f"Arguments:")
            for key, value in step.get("args", {}).items():
                display_value = str(value)
                if len(display_value) > 80:
                    display_value = display_value[:77] + "..."
                print(f"  - {key}: {display_value}")
            
            if "error" in step:
                print(f"Status: ✗ Error - {step['error']}")
            else:
                result_value = step.get("result", {})
                if isinstance(result_value, dict):
                    print(f"Result:")
                    for key, value in result_value.items():
                        display_value = str(value)
                        if len(display_value) > 80:
                            display_value = display_value[:77] + "..."
                        print(f"  - {key}: {display_value}")
                else:
                    print(f"Result: {result_value}")
                print(f"Status: ✓ Completed")
    else:
        print("No steps executed.")


def main():
    """Main entry point for multi-agent execution."""
    if len(sys.argv) < 2:
        print("Usage: python run_multi_agent.py \"<user query>\"")
        print("\nExample:")
        print('  python run_multi_agent.py "Find me a project with a 50x100 layout"')
        sys.exit(1)
    
    user_query = sys.argv[1]
    
    print("=" * 60)
    print("MULTI-AGENT EXECUTION")
    print("=" * 60)
    print(f"\nUser Query: \"{user_query}\"")
    
    # Create specialized agents
    print("\nInitializing specialized agents...")
    search_agent = SearchOrchestrator(tools=ALL_TOOLS)
    print(f"✓ Search Orchestrator ready ({len(ALL_TOOLS)} tools)")
    if search_agent.langgraph_workflow:
        print(f"  ✓ LangGraph workflow built from retrieve_db_info.graph.md")
    elif HAS_LANGGRAPH:
        print(f"  ⚠ LangGraph available but workflow not built")
    else:
        print(f"  ℹ LangGraph not installed - install with: pip install langgraph")
    
    # Create team orchestrator
    team_orchestrator = TeamOrchestrator(
        specialized_agents={
            "search": search_agent,
            # Future: add more specialized agents here
        }
    )
    print("✓ Team Orchestrator ready")
    
    if not team_orchestrator.enabled:
        print("\n❌ AI not enabled. Set OPENAI_API_KEY in .env file")
        sys.exit(1)
    
    # Execute - fast routing + specialized execution
    print("\n" + "=" * 60)
    print("EXECUTING")
    print("=" * 60)
    print("\nRouting task to specialized agent...")
    
    try:
        result = team_orchestrator.execute(user_query)
        
        # Print routing decision
        if result.get("routing"):
            print_routing(result["routing"])
        
        # Print plan from specialized agent
        if result.get("plan"):
            print_plan(result["plan"])
        
        # Print execution trace
        print_execution_trace(result)
        
        # Print final result
        if result.get("results"):
            print("\n" + "=" * 60)
            print("FINAL RESULT")
            print("=" * 60)
            print(result["results"])
        
        if result.get("success"):
            print("\n✓ Execution completed successfully")
            print(f"  Orchestrator: {result.get('orchestrator', 'unknown')}")
            print(f"  Specialized Agent: {result.get('specialized_agent', 'unknown')}")
        else:
            print("\n✗ Execution failed or incomplete")
            if result.get("error"):
                print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

