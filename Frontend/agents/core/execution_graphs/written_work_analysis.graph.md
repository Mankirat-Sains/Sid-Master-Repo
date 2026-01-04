1.
identify_active_document
location: local
capability: document_discovery
produces: document_id | none
IF no document_id is produced
→ request_clarification

request_clarification
location: cloud
input: missing_information (no active document)
output: user_response
terminal: true

read_document
location: local
capability: document_read
input: document_id
produces: extracted_text, extracted_structure

analyze_document_context
location: cloud
input: extracted_text, extracted_structure
produces: document_summary, key_topics, document_intent

retrieve_similar_projects
location: cloud
capability: semantic_search
input: document_summary, key_topics
produces: project_ids, similarity_scores

retrieve_project_artifacts
location: cloud
input: project_ids
produces: reference_documents, completion_notes, outcomes

synthesize_guidance
location: cloud
input: document_summary, reference_documents, outcomes
produces: suggested_content, recommended_structure, follow_up_questions

Validation Notes
- All intents validated against intent_catalog.md
- Missing inputs: none / <list>
- Execution status: ready | blocked | needs_clarification