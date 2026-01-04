"""Semantic planner - converts NL questions to FactPlans"""
import json
import logging
from typing import Optional
import openai
from pathlib import Path

from config import settings
from models.fact_plan import FactPlan

logger = logging.getLogger(__name__)


class SemanticPlanner:
    """Converts natural language questions into structured FactPlans"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "prompt.txt"
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
    
    def plan(self, question: str) -> FactPlan:
        """
        Convert a natural language question into a FactPlan.
        
        Args:
            question: Natural language question
        
        Returns:
            Structured FactPlan
        """
        logger.info("=" * 80)
        logger.info("PLANNER: Starting planning phase")
        logger.info(f"PLANNER: Question: {question}")
        
        # Build prompt
        prompt = self.prompt_template + f"\n\nQuestion: {question}\n\nFactPlan:"
        
        try:
            logger.debug(f"PLANNER: Sending request to LLM (model: {self.model}, temperature: {settings.PLANNER_TEMPERATURE})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a semantic planner. Output ONLY valid JSON, no explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.PLANNER_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content.strip()
            logger.debug(f"PLANNER: Received LLM response (length: {len(content)} chars)")
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                logger.debug("PLANNER: Removed markdown code blocks from response")
            
            # Parse JSON
            logger.debug("PLANNER: Parsing JSON response")
            plan_dict = json.loads(content)
            logger.debug(f"PLANNER: Parsed JSON successfully. Keys: {list(plan_dict.keys())}")
            
            # Validate and create FactPlan
            fact_plan = FactPlan(**plan_dict)
            
            # Log detailed plan information
            logger.info("PLANNER: Generated FactPlan details:")
            logger.info(f"  - Scope: {fact_plan.scope}")
            logger.info(f"  - Number of filters: {len(fact_plan.filters)}")
            logger.info(f"  - Number of aggregations: {len(fact_plan.aggregations)}")
            logger.info(f"  - Number of outputs: {len(fact_plan.outputs)}")
            
            if fact_plan.filters:
                logger.info("PLANNER: Filters:")
                for i, filter_obj in enumerate(fact_plan.filters, 1):
                    logger.info(f"  [{i}] Fact: {filter_obj.fact}, Operator: {filter_obj.op}, Value: {filter_obj.value}")
            
            if fact_plan.aggregations:
                logger.info("PLANNER: Aggregations:")
                for i, agg in enumerate(fact_plan.aggregations, 1):
                    logger.info(f"  [{i}] Type: {agg.type}, Fact: {agg.fact}, By: {agg.by}")
            
            if fact_plan.outputs:
                logger.info(f"PLANNER: Outputs: {fact_plan.outputs}")
            
            logger.info("PLANNER: Planning phase complete")
            logger.info("=" * 80)
            
            return fact_plan
        
        except json.JSONDecodeError as e:
            logger.error(f"PLANNER: Failed to parse JSON from LLM: {e}")
            logger.error(f"PLANNER: Response was: {content}")
            raise ValueError(f"Invalid JSON from planner: {e}")
        except Exception as e:
            logger.error(f"PLANNER: Error in semantic planner: {e}", exc_info=True)
            raise

