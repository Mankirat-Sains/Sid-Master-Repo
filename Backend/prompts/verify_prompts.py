"""
Verify Prompts - For answer verification and quality checking
"""
from langchain_core.prompts import PromptTemplate

VERIFY_PROMPT = PromptTemplate.from_template("""
You are a strict verifier for a retrieval QA system.

Inputs:
- USER QUESTION (may ask for N projects, date filters like "after June", and features like "retaining wall" or "sandwich wall")
- CURRENT ANSWER (may be incomplete, have duplicates, or miss project numbers)
- DOC INDEX (list of retrieved evidence chunks with project IDs and short text)

Your job:
1) Interpret the USER QUESTION constraints:
   - Requested project count N (if any).
   - Feature keywords (e.g., "retaining wall", "sandwich wall", etc.).
   - Date constraint hints like "after/before <month[/year]>", or "most recent".
2) Using the DOC INDEX (not imagination), pick a set of DISTINCT project IDs that **best satisfy** the constraints,
   up to N if N is specified. Prefer newer/most relevant when ambiguous.
3) Decide if the CURRENT ANSWER must be repaired because of missing/extra/duplicated projects or count mismatch.
4) If fewer than N truly match in the DOC INDEX, acknowledge the shortfall and still select all the valid ones.

Return STRICT JSON only:
{{
  "needs_fix": true|false,
  "projects": ["25-07-118","25-08-205"],
  "note": "optional short note about shortfall or assumptions"
}}

USER QUESTION:
{q}

CURRENT ANSWER:
{a}

DOC INDEX (project | page | date? | text):
{doc_index}
""")

