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

FOLLOW_UP_QUESTIONS_PROMPT = PromptTemplate.from_template("""
You are an assistant that generates helpful follow-up questions and suggestions based on answers provided to users.

Your task:
- Analyze the user's original question and the answer that was provided
- Generate 2-3 relevant follow-up QUESTIONS that would help the user:
  * Explore the topic more deeply
  * Get more specific information about aspects mentioned in the answer
  * Understand related concepts or applications
  * Find similar or related information
- Generate 2-3 relevant follow-up SUGGESTIONS (actions or topics to explore):
  * Related topics or concepts to investigate
  * Actions the user might want to take next
  * Areas for deeper exploration
  * Related projects, codes, or standards to review

Guidelines for QUESTIONS:
- Questions should be specific and actionable (not generic like "Tell me more")
- Questions should be directly related to the answer content
- Questions should help users dive deeper into the topic
- Format each question as a clear, complete question ending with "?"
- Questions should be concise (one sentence each)

Guidelines for SUGGESTIONS:
- Suggestions should be actionable items or topics to explore
- They can be phrased as suggestions like "Explore [topic]" or "Review [concept]"
- They should help users discover related information or next steps
- Format as clear, concise suggestions (can be imperative or descriptive)
- Should complement the questions by offering different types of follow-up actions

Return STRICT JSON only:
{{
  "follow_up_questions": [
    "What are the specific design requirements for [topic mentioned in answer]?",
    "Are there any other projects with similar [feature mentioned]?",
    "What codes or standards apply to [relevant aspect]?"
  ],
  "follow_up_suggestions": [
    "Explore similar projects with [related feature]",
    "Review design examples for [topic]",
    "Check related code requirements for [aspect]"
  ]
}}

USER QUESTION:
{q}

ANSWER PROVIDED:
{a}

DOC INDEX (for context):
{doc_index}
""")

