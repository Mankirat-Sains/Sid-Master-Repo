Intent: identify_active_document

Description
Determine whether the user currently has a document open on their local machine and identify it.

Execution Plane
Local

Capability Required
document_discovery

Required Inputs
none

Produced Outputs
document_id
document_type (word | pdf | unknown)
application (word | other)
file_path (if available)

Safety
Read-only

Intent: request_clarification

Execution Plane: 
cloud

Required Inputs: 
missing_fields

Produced Outputs: 
user_response

Safety: 
read-only

Intent: read_document

Description
Read the contents of a specified document without modifying it.

Execution Plane
Local

Capability Required
document_read

Required Inputs
document_id

Produced Outputs
extracted_text
extracted_structure (headings, sections, tables)
document_metadata

Safety
Read-only

Intent: analyze_document_context

Description
Analyze the meaning, purpose, and structure of a document.

Execution Plane
Cloud

Required Inputs
extracted_text
extracted_structure

Produced Outputs
document_summary
key_topics
document_intent (e.g. proposal, report, narrative)

Safety
Read-only

Intent: retrieve_similar_projects

Description
Find past projects or documents that are semantically similar to the current document.

Execution Plane
Cloud

Required Inputs
document_summary
key_topics

Produced Outputs
project_ids
similarity_scores

Safety
Read-only

Intent: retrieve_project_artifacts

Description
Retrieve relevant documents, outcomes, or notes from identified past projects.

Execution Plane
Cloud

Required Inputs
project_ids

Produced Outputs
reference_documents
completion_notes
outcomes

Safety
Read-only

Intent: synthesize_guidance

Description
Combine current document context with past project knowledge to generate guidance for the user.

Execution Plane
Cloud

Required Inputs
document_summary
reference_documents
outcomes

Produced Outputs
suggested_content
recommended_structure
follow_up_questions (if needed)

Safety
Read-only

Intent: extract_search_criteria

Description
Extract structured search constraints from a user query.

Execution Plane
Cloud

Required Inputs
user_query

Produced Outputs
dimension_constraints
additional_filters (if present)

Safety
Read-only

Intent: search_projects_by_dimensions

Description
Search the project database for projects matching dimensional constraints.

Execution Plane
Cloud

Capability Required
structured_query

Required Inputs
dimension_constraints

Produced Outputs
candidate_project_ids
match_scores

Safety
Read-only

Intent: rank_projects_by_similarity

Description
Rank candidate projects by closeness to requested criteria.

Execution Plane
Cloud

Required Inputs
candidate_project_ids
match_scores

Produced Outputs
ranked_project_ids

Safety
Read-only

Intent: retrieve_project_metadata

Description
Retrieve summary metadata for selected projects.

Execution Plane
Cloud

Required Inputs
ranked_project_ids

Produced Outputs
project_summaries

Safety
Read-only