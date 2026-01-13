# Scenario Router

This file defines how user scenarios are mapped to execution graphs.

---

## Scenario: find_past_project

**Description**
User is requesting historical project information based on structured criteria.

**Triggers**
- Mentions of dimensions (e.g. "40x80", "40' x 80'")
- Requests for past or existing projects
- No reference to an active local document

**Mapped Plan**
retrieve_db_info.plan.md

**Mapped Execution Graph**
retrieve_db_info.graph.md

**Execution Mode**
Cloud-only

---

## Scenario: rfp_response

**Description**
User is asking for help responding to or improving written work.

**Triggers**
- References to RFPs, proposals, reports
- Mentions of reviewing or improving text
- Active document may be present

**Mapped Plan**
written_work_improvement.plan.md

**Mapped Execution Graph**
written_work_analysis.graph.md

**Execution Mode**
Hybrid (local + cloud)
