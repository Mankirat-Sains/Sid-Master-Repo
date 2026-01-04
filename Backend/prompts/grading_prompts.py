"""
Grading Prompts - For relevance grading of retrieved chunks
"""
from langchain_core.prompts import PromptTemplate
from config.llm_instances import llm_grader

SELF_GRADE_PROMPT = PromptTemplate.from_template(
    "Question:\n{q}\n\nChunk:\n{chunk}\n\n"
    "Is this chunk directly useful to answer the question? "
    "Answer 'yes' or 'no' only."
)

BATCH_GRADE_PROMPT = PromptTemplate.from_template(
    "Question:\n{q}\n\n"
    "Chunks:\n{chunks}\n\n"
    "Rate each chunk as 'yes' if it contains ANY information relevant to the question, even if indirect. "
    "Be generous - include chunks that mention related terms, project details, or context. "
    "For each chunk, respond ONLY with 'yes' or 'no', one per line, matching the order of chunks."
)

# Export the grader LLM instance
grading_llm = llm_grader

