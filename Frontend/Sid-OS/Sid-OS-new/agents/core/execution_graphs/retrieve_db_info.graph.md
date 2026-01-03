1.
extract_search_criteria
location: cloud
input: user_query
produces: dimension_constraints

IF dimension_constraints are incomplete
→ request_clarification

request_clarification
location: cloud
input: missing_fields (dimensions, building type, material)
output: user_response
terminal: true

search_projects_by_dimensions
location: cloud
capability: structured_query
input: dimension_constraints
produces: candidate_project_ids, match_scores

rank_projects_by_similarity
location: cloud
input: candidate_project_ids, match_scores
produces: ranked_project_ids

retrieve_project_metadata
location: cloud
input: ranked_project_ids
produces: project_summaries

Validation Notes
- All intents validated against intent_catalog.md
- Missing inputs: none
- Execution status: ready | needs_clarification
