# Document Generation System Revamp - Implementation Specification

## Executive Summary

**Current Problem:**
The system generates documents by retrieving individual sections (introduction, conclusion, etc.) from a database, but it doesn't understand the **complete structure** of company-specific document types. When a user asks to "create a report," the system doesn't know which sections that company's reports typically contain, in what order, or with what styling conventions.

**Proposed Solution:**
Transform the document generation system into a **section-by-section interactive workflow** where:
1. The system learns and stores complete document templates per company (which sections exist, in what order, with what styling)
2. When generating a document, it identifies all required sections for that document type
3. For each section, it generates content using company-specific embeddings and style patterns
4. After generating each section, it presents the draft to the user for approval/feedback/rejection
5. Only upon approval does it write the section to the actual document
6. The process continues iteratively until the entire document is complete

---

## I. What You're Asking For (Restated)

### Core Requirements

1. **Company-Specific Document Structure Storage**
   - Store complete document templates: "Company X's reports have: Executive Summary, Introduction, Methodology, Findings, Calculations, Recommendations, Conclusion"
   - Store section metadata: required vs optional, typical length, position/order, formatting rules
   - Store section interdependencies: "Conclusion must reference Findings and Recommendations"

2. **Template-Driven Generation**
   - User asks: "Generate a Q4 Safety Report"
   - System identifies: "Safety Report for this company has 7 sections"
   - System generates each section in sequence, not all at once

3. **Human-in-the-Loop Per Section**
   - Generate Introduction → Show to user → Wait for approval
   - If approved → Write to document → Generate next section
   - If feedback → Regenerate with feedback → Show again
   - If rejected → Skip or mark for later → Continue

4. **Intelligent Section Generation**
   - Each section uses company-specific embeddings for content
   - Each section uses company-specific style patterns
   - Each section is contextually aware of previously approved sections

5. **Flexible Document Structures**
   - Some companies have "Calculations" sections, some don't
   - Some companies use "Executive Summary," others use "Abstract"
   - System adapts to each company's conventions

---

## II. Current System Analysis

### What Exists Today

**Storage Layer:**
- **Supabase Vector Store:** Stores chunks with embeddings
  - Columns: `id`, `content`, `embedding`, `artifact_id`, `version_id`, `company_id`, `chunk_type` (content/style), `section_type`, `doc_type`, `source`, `file_path`, `heading`, `page_number`
  - Retrieves top-k similar chunks for a given query
  
- **SQLite Metadata DB:** Stores document and chunk metadata
  - `documents` table: document-level info (artifact_id, company_id, file_name, doc_type, etc.)
  - `chunks` table: chunk-level details (section_type, chunk_type, style_frequency, quality_score, etc.)
  - Used for section-length profiling and style frequency lookups

**Generation Flow:**
1. User query → `doc_task_classifier` identifies docgen need
2. Routed to `docgen_subgraph` or deep desktop loop
3. `Tier2 generator` retrieves content chunks (top-k=10) and style chunks (top-k=4)
4. Filters by company → doc_type → section_type
5. Generates **entire draft** in one pass
6. Returns `doc_generation_result` with full text + citations
7. API materializes DOCX with all sections at once
8. User sees completed document

**Interrupt System:**
- Currently only for **destructive actions** (write_file, delete_file, materialize_doc)
- Not section-aware
- All-or-nothing approval

### What's Missing

1. **No Document Template Storage**
   - System doesn't know "Company A's reports always have sections X, Y, Z in that order"
   - Section discovery is ad-hoc based on retrieved chunks

2. **No Section-Level Workflow**
   - Generates entire document in one shot
   - No incremental approval/feedback loop

3. **No Section Dependency Tracking**
   - Can't generate "Conclusion" that references approved "Findings"
   - No awareness of section ordering or relationships

4. **Limited Style Learning**
   - Style chunks exist but aren't systematically mapped to document templates
   - No "Company X always uses bullet lists in Recommendations" rules

5. **Interrupt System Not Section-Aware**
   - Current interrupts are for file operations, not content approval
   - No feedback mechanism beyond approve/reject

---

## III. Proposed Architecture Changes

### A. New Database Schema

#### 1. Document Templates Table
**Purpose:** Store the canonical structure of document types per company

```
document_templates:
  - template_id (PK)
  - company_id (FK)
  - doc_type (e.g., "Safety Report", "Technical Specification", "Executive Summary")
  - template_name (e.g., "Standard Safety Report v2.1")
  - version
  - is_active (boolean - only one active template per company+doc_type)
  - created_at
  - created_by
  - metadata (JSON: additional styling rules, formatting preferences)
```

#### 2. Template Sections Table
**Purpose:** Define which sections belong to each template and their properties

```
template_sections:
  - section_id (PK)
  - template_id (FK)
  - section_name (e.g., "Introduction", "Methodology", "Conclusions")
  - section_type (standardized: intro, body, conclusion, calculations, etc.)
  - position_order (integer: 1, 2, 3... for ordering)
  - is_required (boolean)
  - is_optional (boolean)
  - depends_on_sections (JSON array: ["findings", "recommendations"])
  - min_length_chars
  - max_length_chars
  - typical_length_chars (calculated from historical data)
  - style_guidelines (JSON: bullet_points: true, tables: false, etc.)
  - heading_level (1, 2, 3 for H1, H2, H3)
  - section_prompt_template (custom prompt instructions for this section)
  - metadata (JSON: additional rules)
```

#### 3. Section Style Patterns Table
**Purpose:** Store learned style patterns for each section type per company

```
section_style_patterns:
  - pattern_id (PK)
  - company_id (FK)
  - section_type (FK to template_sections)
  - doc_type
  - pattern_type (e.g., "tone", "formatting", "terminology", "structure")
  - pattern_description (e.g., "Always uses passive voice in Methodology")
  - example_chunk_ids (JSON array of chunk_ids that exemplify this pattern)
  - confidence_score (0-1, based on how often pattern appears)
  - learned_from_count (how many documents contributed to this pattern)
  - last_updated
```

#### 4. Document Generation Sessions Table
**Purpose:** Track multi-step document generation workflows

```
generation_sessions:
  - session_id (PK)
  - user_id
  - company_id
  - template_id (FK)
  - doc_type
  - target_filename
  - status (in_progress, completed, cancelled)
  - current_section_id (FK - which section we're working on)
  - created_at
  - completed_at
  - workspace_path (where draft is being assembled)
  - metadata (JSON: user preferences, overrides)
```

#### 5. Section Generation History Table
**Purpose:** Track each section's generation, feedback, and approval history

```
section_generation_history:
  - generation_id (PK)
  - session_id (FK)
  - section_id (FK to template_sections)
  - section_name
  - attempt_number (1, 2, 3... for regenerations)
  - generated_content (text)
  - content_length_chars
  - citations (JSON array)
  - retrieval_metadata (JSON: chunks used, scores, mode)
  - status (pending_review, approved, rejected, needs_revision)
  - user_feedback (text)
  - approval_timestamp
  - approved_by_user_id
  - generation_timestamp
  - model_used
  - generation_params (JSON: temperature, etc.)
```

---

### B. Enhanced Vector Storage Strategy

#### What to Embed vs Store Directly

**Embed (Vector Storage):**
1. **Content Chunks** (as currently done)
   - Actual paragraphs/sentences from documents
   - With metadata: company_id, doc_type, section_type, artifact_id
   - Enable semantic search for relevant content

2. **Section Introductions/Conclusions** (NEW)
   - First and last paragraphs of each section type
   - Helps model learn how to open/close sections in company style

3. **Style Exemplars** (ENHANCED)
   - High-quality example paragraphs tagged by style attributes
   - E.g., "formal technical writing", "bullet-point recommendations", "data-heavy findings"

4. **Section Transitions** (NEW)
   - Sentences that bridge between sections
   - Helps maintain document flow and coherence

**Store Directly (Structured DB):**
1. **Document Templates** (new tables above)
   - Not embedded because we need exact matches and relationships
   - Queried by company_id + doc_type

2. **Section Metadata** (enhanced)
   - Length statistics, position, dependencies
   - Relational data, not suitable for embedding

3. **Style Rules** (new table above)
   - Explicit rules: "Use tables for calculations", "Avoid jargon in Executive Summary"
   - Discrete facts, not semantic similarity

4. **User Feedback & Approvals** (new history table)
   - Audit trail for compliance and learning
   - Not for semantic search

---

### C. New Workflow Architecture

#### Phase 1: Template Initialization (One-time per company/doc_type)

**Process:**
1. **Analyze Existing Documents**
   - Scan all company documents of type "Safety Report"
   - Extract section headings, ordering, and frequency
   - Calculate typical section lengths
   - Identify common style patterns

2. **Create Template**
   - Insert into `document_templates` table
   - Create `template_sections` entries for each discovered section
   - Generate `section_style_patterns` from analysis

3. **Learn Style Patterns**
   - For each section type, identify:
     - Tone (formal, technical, conversational)
     - Structure (paragraphs, bullets, tables)
     - Terminology (industry-specific terms)
     - Formatting (bold headers, italics, numbering)

**Fallback:**
- If no company documents exist yet, use industry-standard templates
- Mark as "default template" and update as documents are added

---

#### Phase 2: Document Generation Workflow (Per User Request)

**Step 1: Template Selection**
```
User: "Generate a Q4 Safety Report"
System:
  1. Extract doc_type: "Safety Report"
  2. Query: SELECT * FROM document_templates 
     WHERE company_id = X AND doc_type = 'Safety Report' AND is_active = true
  3. Retrieve template with all sections ordered by position_order
  4. Create generation_session record
```

**Step 2: Section Queue Creation**
```
System:
  1. Build ordered list of sections from template
  2. Filter out optional sections if user preferences indicate
  3. Store in session state: sections_to_generate = [sec1, sec2, sec3...]
  4. Set current_section = sections_to_generate[0]
```

**Step 3: Iterative Section Generation Loop**
```
FOR EACH section in sections_to_generate:
  
  A. Pre-Generation Context Building
     - Retrieve all previously approved sections from this session
     - Build context: "You're writing [section_name]. Previous sections covered..."
     - Check dependencies: if section depends on [X], ensure [X] is approved
  
  B. Retrieval Phase
     - Query vector store for content chunks:
       * Filters: company_id, doc_type, section_type=[current section]
       * Include previously approved section content as context
     - Query for style chunks specific to this section type
     - Retrieve section_style_patterns for this section
  
  C. Generation Phase
     - Build prompt with:
       * Section requirements from template
       * Retrieved content chunks
       * Style patterns and guidelines
       * Previously approved sections (for context/consistency)
       * User's original query/requirements
     - Generate draft text
     - Apply length constraints from template
     - Format according to style guidelines
  
  D. INTERRUPT: Present to User
     - Emit interrupt event with:
       * section_name
       * generated_content
       * citations
       * retrieval_metadata (what was used)
       * actions: [approve, request_feedback, reject, skip]
     - Pause graph execution
     - Wait for user response via /approve-section endpoint
  
  E. Handle User Response
     
     IF approved:
       - Save to section_generation_history with status='approved'
       - Write section to workspace document
       - Move to next section
     
     IF feedback provided:
       - Save feedback to section_generation_history
       - Increment attempt_number
       - Regenerate with feedback incorporated
       - GOTO step D (present again)
     
     IF rejected:
       - Mark section status='rejected'
       - Options:
         a) Skip section (if optional)
         b) Try different retrieval strategy
         c) Ask user to provide content manually
     
     IF skip requested:
       - Mark section status='skipped'
       - Continue to next section

  F. Update Session State
     - Update current_section_id to next section
     - Append approved content to cumulative document context

END LOOP
```

**Step 4: Document Finalization**
```
System:
  1. Assemble all approved sections into final document
  2. Apply document-level formatting
  3. Generate table of contents
  4. Materialize DOCX via existing OnlyOffice integration
  5. Mark generation_session status='completed'
  6. Present final document to user
```

---

### D. Interrupt System Enhancement

#### New Interrupt Types

**1. Section Approval Interrupt**
```json
{
  "type": "section_approval",
  "session_id": "gen_12345",
  "section_id": "intro_789",
  "section_name": "Introduction",
  "section_order": 1,
  "total_sections": 7,
  "generated_content": "...",
  "length_chars": 450,
  "target_length": {"min": 400, "max": 600},
  "citations": [...],
  "retrieval_mode": "retrieved",
  "actions": [
    {
      "action": "approve",
      "label": "Approve & Continue",
      "description": "Accept this section and move to next"
    },
    {
      "action": "feedback",
      "label": "Request Changes",
      "description": "Provide feedback to regenerate this section",
      "requires_input": true
    },
    {
      "action": "reject",
      "label": "Reject Section",
      "description": "Skip this section or provide content manually"
    }
  ]
}
```

**2. Template Selection Interrupt** (Optional)
```json
{
  "type": "template_selection",
  "available_templates": [
    {"template_id": "tpl_1", "name": "Standard Safety Report", "sections": 7},
    {"template_id": "tpl_2", "name": "Brief Safety Report", "sections": 4}
  ],
  "recommended": "tpl_1",
  "actions": ["select", "customize"]
}
```

#### API Endpoints Enhancement

**New: `/approve-section`**
```
POST /approve-section
{
  "session_id": "gen_12345",
  "section_id": "intro_789",
  "generation_id": "hist_456",
  "action": "approve" | "feedback" | "reject" | "skip",
  "feedback_text": "Make it more concise and add safety statistics",
  "user_id": "user_123"
}

Response:
{
  "status": "ok",
  "next_section": {
    "section_id": "method_790",
    "section_name": "Methodology",
    "position": 2
  },
  "session_status": "in_progress",
  "progress": {
    "completed": 1,
    "total": 7,
    "percentage": 14
  }
}
```

**Enhanced: `/chat/stream`**
```
SSE Events:
- type: "section_generation_start" - section generation begins
- type: "retrieval_complete" - chunks retrieved
- type: "section_draft_ready" - draft text generated
- type: "section_approval_interrupt" - waiting for user approval
- type: "section_approved" - user approved, moving to next
- type: "section_regenerating" - regenerating with feedback
- type: "document_complete" - all sections approved
```

---

## IV. Implementation Phases

### Phase 1: Database & Storage (Week 1-2)
1. Create new database tables (document_templates, template_sections, section_style_patterns, generation_sessions, section_generation_history)
2. Add migration scripts
3. Enhance vector store schema with new metadata fields
4. Create data models in Python (SQLAlchemy/Pydantic)

### Phase 2: Template Learning (Week 3-4)
1. Build document analyzer to extract section structures from existing documents
2. Create template creation API endpoints
3. Implement style pattern learning algorithm
4. Add admin UI for template management (optional)

### Phase 3: Section-by-Section Generation (Week 5-7)
1. Refactor Tier2 generator to support single-section generation
2. Implement section context building (using previous sections)
3. Add section dependency checking
4. Create generation session management

### Phase 4: Interrupt Integration (Week 8-9)
1. Extend interrupt system for section approvals
2. Create `/approve-section` endpoint
3. Enhance SSE event types in `/chat/stream`
4. Update state management to track section-level approvals

### Phase 5: Frontend Integration (Week 10-11)
1. Create section-by-section review UI component
2. Add progress indicators
3. Implement feedback input mechanism
4. Integrate with existing DocumentPreviewPanel

### Phase 6: Testing & Refinement (Week 12)
1. End-to-end testing with real company documents
2. Performance optimization
3. Edge case handling
4. Documentation

---

## V. Key Design Decisions

### 1. Section Order Enforcement
**Decision:** Strictly follow template order but allow user to skip optional sections
**Rationale:** Maintains document coherence; later sections can reference earlier ones

### 2. Section Regeneration Limits
**Decision:** Allow up to 3 regeneration attempts per section before requiring manual intervention
**Rationale:** Prevent infinite loops; user can provide more context or skip

### 3. Context Window Management
**Decision:** Pass all previously approved sections as context to next section generation
**Rationale:** Ensures consistency and allows cross-references

**Caveat:** May hit context limits for long documents
**Solution:** Summarize older sections or use section summaries

### 4. Template Update Strategy
**Decision:** Templates are versioned; updates create new version, don't modify active template
**Rationale:** Preserves audit trail; allows rollback

### 5. Embedding Strategy
**Decision:** Keep existing content embeddings; add new embeddings for section transitions and style exemplars
**Rationale:** Builds on existing investment; enhances without disrupting

---

## VI. Open Questions & Considerations

### 1. What if user wants to add a section not in template?
**Options:**
- A) Allow ad-hoc section insertion with custom prompt
- B) Suggest updating template for future use
- C) Both

**Recommendation:** Both - allow flexibility but encourage template refinement

### 2. How to handle cross-company document generation?
**Scenario:** User wants "a report like Company A creates but for Company B"

**Options:**
- A) Use Company A's template with Company B's content embeddings
- B) Blend templates
- C) Explicit template selection

**Recommendation:** Option C - let user explicitly select template, then use target company's embeddings

### 3. Should system auto-improve templates based on user feedback?
**Scenario:** User consistently rejects "Calculations" section in reports

**Options:**
- A) Auto-mark section as optional after N rejections
- B) Suggest template update to admin
- C) Learn user preferences per-user

**Recommendation:** Option B initially; Option C for future enhancement

### 4. How to handle real-time collaboration?
**Scenario:** Multiple users editing same document generation session

**Options:**
- A) Lock session to one user
- B) Merge approvals (requires consensus)
- C) Branch sessions

**Recommendation:** Option A for MVP; revisit for enterprise features

---

## VII. Success Metrics

### System Performance
- Template creation time: < 30 seconds for 10-page document analysis
- Section generation time: < 10 seconds per section
- User approval/feedback latency: < 2 seconds

### User Experience
- Approval rate: > 80% of sections approved on first attempt
- Regeneration rate: < 20% of sections require feedback
- Completion rate: > 90% of started sessions complete

### Quality
- Citation accuracy: > 95% of citations traceable to source
- Style consistency: > 85% match to company style patterns (measured by style validator)
- Length compliance: > 90% of sections within target length range

---

## VIII. Risks & Mitigations

### Risk 1: Context Window Overflow
**Impact:** Cannot pass all previous sections to later sections
**Mitigation:** Implement section summarization; use compressed context

### Risk 2: User Fatigue
**Impact:** Users abandon after approving 3-4 sections
**Mitigation:** 
- Batch approval option for trusted sections
- "Auto-approve" mode with post-generation review
- Progress indicators and time estimates

### Risk 3: Template Overfitting
**Impact:** Templates too rigid, don't adapt to new document needs
**Mitigation:**
- Support template variants
- Easy template override mechanism
- Regular template review prompts

### Risk 4: Dependency Deadlocks
**Impact:** Section A depends on Section C but C depends on A
**Mitigation:** Validate template dependencies during creation; prevent cycles

---

## IX. Migration Path from Current System

### Backward Compatibility
**Requirement:** Existing one-shot document generation must still work

**Strategy:**
1. Add feature flag: `SECTION_BY_SECTION_GENERATION` (default: false)
2. If false, use existing flow
3. If true, use new template-driven flow
4. Gradual rollout: test with pilot companies first

### Template Bootstrapping
**For companies with existing documents:**
1. Run analyzer on existing documents
2. Generate templates automatically
3. Human review and refinement
4. Mark as active

**For new companies:**
1. Provide industry-standard templates
2. Customize as documents are created
3. Learn patterns from first 5-10 documents

---

## X. Next Steps

1. **Review & Approval**
   - Stakeholder review of this specification
   - Identify any missing requirements
   - Prioritize features (MVP vs future enhancements)

2. **Technical Design**
   - Detailed database schema SQL
   - API endpoint specifications (OpenAPI)
   - State machine diagrams for generation workflow
   - Component architecture diagrams

3. **Prototype**
   - Build minimal template storage
   - Implement single-section generation with interrupt
   - Test with one company's documents

4. **Feedback & Iterate**
   - User testing with prototype
   - Refine based on real usage
   - Adjust scope for Phase 1 release

---

## Summary

This specification outlines a transformation of the document generation system from **monolithic batch generation** to **iterative, template-driven, human-in-the-loop creation**. 

**Core innovations:**
- Company-specific document templates defining structure and style
- Section-by-section generation with approval gates
- Context-aware generation using previously approved content
- Enhanced interrupt system for granular control
- Structured storage of templates, patterns, and generation history

**Key benefits:**
- Higher quality output (user validates each section)
- Better style consistency (learned patterns per company)
- Flexibility (skip, customize, regenerate sections individually)
- Audit trail (full history of generation and approvals)
- Scalability (templates reusable across many documents)

This approach positions the system as an **intelligent document co-pilot** rather than a one-shot generator, fundamentally changing the user experience from "hope it's good" to "collaboratively refine."
