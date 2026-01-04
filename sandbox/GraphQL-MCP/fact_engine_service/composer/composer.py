"""Answer composer - synthesizes facts into human-readable answers"""
import json
import logging
from pathlib import Path
import openai

from config import settings
from models.fact_result import FactResult
from models.answer import Answer

logger = logging.getLogger(__name__)


class AnswerComposer:
    """Composes human-readable answers from extracted facts"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "prompt.txt"
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
    
    def compose(self, question: str, fact_result: FactResult) -> Answer:
        """
        Compose a human-readable answer from extracted facts.
        
        Args:
            question: Original user question
            fact_result: Extracted facts
        
        Returns:
            Composed answer with explanation
        """
        logger.info("=" * 80)
        logger.info("COMPOSER: Starting composition phase")
        logger.info(f"COMPOSER: Question: {question}")
        logger.info(f"COMPOSER: Fact result - {len(fact_result.projects)} projects, {fact_result.total_elements_processed} elements processed")
        
        # Format facts for LLM
        logger.info("COMPOSER: Formatting facts for LLM")
        facts_str = self._format_facts(fact_result)
        logger.debug(f"COMPOSER: Formatted facts (length: {len(facts_str)} chars)")
        
        # Build prompt - use replace instead of format to avoid issues with JSON braces
        prompt = self.prompt_template.replace("{question}", question).replace("{facts}", facts_str)
        logger.debug(f"COMPOSER: Built prompt (length: {len(prompt)} chars)")
        
        try:
            logger.info(f"COMPOSER: Sending request to LLM (model: {self.model}, temperature: {settings.COMPOSER_TEMPERATURE})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an answer composer for structural engineering questions. Provide clear, factual answers with explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.COMPOSER_TEMPERATURE
            )
            
            answer_text = response.choices[0].message.content.strip()
            logger.info(f"COMPOSER: Received LLM response (length: {len(answer_text)} chars)")
            logger.debug(f"COMPOSER: Answer text: {answer_text[:200]}..." if len(answer_text) > 200 else f"COMPOSER: Answer text: {answer_text}")
            
            # Parse structured answer (try to extract components)
            logger.info("COMPOSER: Parsing answer")
            answer = self._parse_answer(answer_text, fact_result)
            
            logger.info(f"COMPOSER: Composed answer with confidence {answer.confidence}")
            logger.info(f"COMPOSER: Answer has {len(answer.supporting_facts)} supporting facts")
            logger.info(f"COMPOSER: Answer covers {answer.project_count} projects")
            logger.info("COMPOSER: Composition phase complete")
            logger.info("=" * 80)
            
            return answer
        
        except Exception as e:
            logger.error(f"COMPOSER: Error in answer composer: {e}", exc_info=True)
            # Fallback answer
            return Answer(
                answer="I encountered an error while composing the answer.",
                explanation=str(e),
                confidence=0.0,
                uncertainty="Error occurred during answer composition"
            )
    
    def _format_facts(self, fact_result: FactResult) -> str:
        """Format facts for LLM consumption"""
        facts_dict = {
            "projects": {
                pid: {
                    "project_name": proj.project_name,
                    "project_number": proj.project_number,
                    "elements": proj.elements,
                    "systems": proj.systems,
                    "summary": proj.summary,
                    "confidence": proj.confidence,
                    "evidence_count": len(proj.evidence)
                }
                for pid, proj in fact_result.projects.items()
            },
            "global_facts": fact_result.global_facts,
            "execution_time_ms": fact_result.execution_time_ms,
            "total_elements_processed": fact_result.total_elements_processed
        }
        
        return json.dumps(facts_dict, indent=2)
    
    def _parse_answer(self, answer_text: str, fact_result: FactResult) -> Answer:
        """Parse LLM response into structured Answer"""
        logger.debug("COMPOSER: Parsing answer - computing confidence")
        # Compute overall confidence
        if fact_result.projects:
            confidences = [
                proj.confidence for proj in fact_result.projects.values()
                if proj.confidence > 0
            ]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                logger.debug(f"COMPOSER: Parsing - computed confidence from project confidences: {avg_confidence:.2f}")
            else:
                # If we searched but found nothing, that's actually high confidence in the negative result
                # (assuming we searched a reasonable dataset)
                if fact_result.total_elements_processed > 0:
                    avg_confidence = 0.8  # High confidence we searched and found nothing
                    logger.debug(f"COMPOSER: Parsing - no project confidences, but processed {fact_result.total_elements_processed} elements, using confidence 0.8")
                else:
                    avg_confidence = 0.3  # Low confidence - didn't search much
                    logger.debug("COMPOSER: Parsing - no project confidences and no elements processed, using confidence 0.3")
        else:
            # No projects found - low confidence
            avg_confidence = 0.2
            logger.debug("COMPOSER: Parsing - no projects found, using confidence 0.2")
        
        # Extract key facts
        logger.debug("COMPOSER: Parsing - extracting supporting facts")
        supporting_facts = []
        for proj in fact_result.projects.values():
            if proj.project_name:
                supporting_facts.append(f"Project: {proj.project_name}")
            for elem_type, materials in proj.elements.items():
                for material, count in materials.items():
                    if count > 0:
                        supporting_facts.append(f"{count} {material} {elem_type}s")
        
        logger.debug(f"COMPOSER: Parsing - extracted {len(supporting_facts)} supporting facts")
        
        # Simple parsing - in production, use more sophisticated extraction
        answer = Answer(
            answer=answer_text,
            explanation=answer_text,  # LLM should include explanation in answer
            confidence=avg_confidence,
            supporting_facts=supporting_facts[:10],  # Limit to 10
            project_count=len(fact_result.projects)
        )
        
        logger.debug(f"COMPOSER: Parsing - created Answer object with {len(answer.supporting_facts)} supporting facts")
        return answer

