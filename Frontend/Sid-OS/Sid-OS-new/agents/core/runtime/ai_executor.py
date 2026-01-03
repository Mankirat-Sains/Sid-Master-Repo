"""
Minimal AI executor - replaces simulation for ONE intent.
This proves MD → AI execution works without building the full folder structure.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from project root (go up from localagent/core/runtime to Sid-OS-new)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try current directory
        load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# Use OpenAI or Anthropic - your choice
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class SimpleAIExecutor:
    """Executes ONE intent using AI. Minimal implementation to prove concept."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Try to load from .env if not provided
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = api_key
        if HAS_OPENAI and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
            except Exception:
                self.enabled = False
        else:
            self.enabled = False
    
    def execute_intent(self, intent_name: str, intent_def, inputs: Dict[str, str]) -> Dict[str, str]:
        """
        Execute an intent using AI.
        Only works for extract_search_criteria for now - proves the concept.
        """
        if not self.enabled:
            return {}
        
        if intent_name == "extract_search_criteria":
            return self._extract_search_criteria(inputs)
        
        # For other intents, return empty (fall back to simulation)
        return {}
    
    def _extract_search_criteria(self, inputs: Dict[str, str]) -> Dict[str, str]:
        """Use AI to extract search criteria from user query."""
        user_query = inputs.get("user_query", "")
        
        prompt = f"""Extract search criteria from this user query: "{user_query}"

Return a JSON object with:
- dimension_constraints: object with "dimensions" (string like "50x100") and "complete" (boolean indicating if dimensions are sufficient)
- additional_filters: array of any other filters mentioned (building type, material, etc.)

Example for "Find me a project with a 50x100 layout":
{{
  "dimension_constraints": {{
    "dimensions": "50x100",
    "complete": true
  }},
  "additional_filters": []
}}

Example for "Find me a project":
{{
  "dimension_constraints": {{
    "dimensions": null,
    "complete": false
  }},
  "additional_filters": []
}}

Return ONLY valid JSON, no other text."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheap and fast
                messages=[
                    {"role": "system", "content": "You extract structured search criteria from user queries. Return only valid JSON, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            # Convert to expected format (matching simulate_output format)
            dim_constraints = result.get("dimension_constraints", {})
            dims = dim_constraints.get("dimensions", "unknown")
            complete = dim_constraints.get("complete", False)
            
            outputs = {
                "dimension_constraints": f"{{ dimensions: '{dims}', complete: {str(complete).lower()} }}",
                "additional_filters (if present)": json.dumps(result.get("additional_filters", []))
            }
            
            return outputs
            
        except Exception as e:
            print(f"⚠ AI execution failed: {e} (falling back to simulation)")
            return {}

