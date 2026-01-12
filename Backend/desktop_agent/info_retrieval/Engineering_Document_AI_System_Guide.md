# Engineering Document AI System - Complete Implementation Guide

**Version**: 1.0  
**Last Updated**: January 2026  
**System Name**: DocIntel (Engineering Document Intelligence Platform)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
5. [Core Components Deep Dive](#core-components-deep-dive)
6. [Data Models & Schemas](#data-models--schemas)
7. [API Specifications](#api-specifications)
8. [Desktop Agent Architecture](#desktop-agent-architecture)
9. [Security & Compliance](#security--compliance)
10. [Deployment Strategy](#deployment-strategy)
11. [Testing & Quality Assurance](#testing--quality-assurance)
12. [Performance Optimization](#performance-optimization)
13. [Monitoring & Observability](#monitoring--observability)
14. [Cost Analysis](#cost-analysis)
15. [Appendices](#appendices)

---

## Executive Summary

### What We're Building

An AI-powered system that learns how engineering companies write technical documents by ingesting existing Word/PDF files, extracting structure and style, and enabling intelligent document generation that matches company standards.

### Key Capabilities

- **Intelligent Ingestion**: Parse .docx and .pdf files, extract structure, content, and metadata
- **Dual-Mode Retrieval**: Separate content (factual) and style (curated exemplar) retrieval systems
- **Company-Specific Learning**: Per-company collections/namespaces in a single Qdrant instance (one cluster, many collections)
- **RAG-Powered Generation**: Draft new documents using retrieved examples
- **Desktop Integration**: Bidirectional sync between web platform and local Word/Excel
- **Version Control**: Git-like versioning for engineering documents
- **Template Management**: Automatic extraction and management of document templates
- **Optional Style Fine-Tuning (Tier 3+)**: LoRA adapters only when RAG/template quality is insufficient

### Success Metrics

- **Retrieval Quality**: Top-5 accuracy > 85% for relevant chunks
- **Generation Quality**: 70%+ of generated content requires minimal editing
- **Adoption**: 80%+ of engineers using the system within 6 months
- **Time Savings**: 40% reduction in document drafting time
- **Cost**: < $2 per document generated (all-in infrastructure cost)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│   Web App   │  Desktop App │  Word Add-in │    Developer CLI   │
└─────────────┴──────────────┴──────────────┴────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Gateway Layer                          │
│  Authentication │ Rate Limiting │ Request Routing │ Logging     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Services                        │
├─────────────────┬──────────────────┬──────────────────────────┤
│  Ingest Service │ Retrieval Service│  Generation Service      │
│  - Doc parsing  │  - Content RAG   │  - LLM orchestration     │
│  - Chunking     │  - Style RAG     │  - Template selection    │
│  - Embedding    │  - Hybrid search │  - Quality checks        │
└─────────────────┴──────────────────┴──────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│  Vector DB   │ Metadata DB  │  Object Store│  Cache Layer     │
│  (Qdrant)    │ (Postgres)   │  (S3/MinIO)  │  (Redis)         │
│              │              │              │                  │
│ Collections: │ Tables:      │ Buckets:     │ Keys:            │
│ - content_*  │ - documents  │ - originals  │ - embeddings     │
│ - style_*    │ - chunks     │ - processed  │ - search results │
│              │ - templates  │ - versions   │ - sessions       │
└──────────────┴──────────────┴──────────────┴──────────────────┘

**Multi-Tenancy Model**
- Single Qdrant cluster serves all companies
- Isolation via collection naming: `content_{company_id}`, `style_{company_id}`
- Payload-level filtering for additional security
- NOT separate database deployments per company
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
├─────────────────┬──────────────────┬──────────────────────────┤
│  LLM Providers  │  Cloud Storage   │  Authentication          │
│  - OpenAI       │  - AWS S3        │  - Auth0 / Clerk         │
│  - Anthropic    │  - Google Drive  │  - SSO Integration       │
│  - Local Models │  - OneDrive      │                          │
└─────────────────┴──────────────────┴──────────────────────────┘
```

### Data Flow Architecture

#### Ingestion Pipeline

```
┌──────────────┐
│ Upload Doc   │
│ (.docx/.pdf) │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Document Parser          │
│ - Extract text           │
│ - Extract structure      │
│ - Extract metadata       │
│ - Generate artifact_id   │
│ - Calculate version_id   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Rules-Based Classifier   │
│ - Identify doc_type      │
│ - Classify sections      │
│ - Extract project info   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Smart Chunker            │
│ - Section-based chunks   │
│ - Classify: content/style│
│ - Preserve context       │
│ - Style units are curated exemplars/templates (not full raw chunks) │
└──────┬───────────────────┘
       │
       ├─────────────┬──────────────┐
       ▼             ▼              ▼
┌─────────────┐ ┌──────────┐ ┌────────────┐
│Content Chunk│ │Style Chunk│ │Metadata DB │
└─────┬───────┘ └────┬─────┘ └────────────┘
      │              │
      ▼              ▼
┌──────────────────────────┐
│ Embedding Service        │
│ - Batch processing       │
│ - text-embedding-3-small │
└──────┬───────────────────┘
       │
       ├─────────────┬──────────────┐
       ▼             ▼              │
┌─────────────┐ ┌──────────┐      │
│content_{co} │ │style_{co}│      │
│Vector DB    │ │Vector DB │      │
└─────────────┘ └──────────┘      │
                                   │
                                   ▼
                            ┌──────────────┐
                            │ Indexing     │
                            │ Complete     │
                            └──────────────┘
```

#### Retrieval & Generation Pipeline

```
┌──────────────────────────┐
│ User Query/Request       │
│ "Draft methodology for   │
│  thermal analysis"       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Query Analyzer           │
│ - Identify doc_type      │
│ - Identify section_type  │
│ - Detect engineering_function (justify/summarize/pass-fail/cite codes) │
│ - Extract constraints    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Template Selector        │
│ - Match to template      │
│ - Get section structure  │
└──────┬───────────────────┘
       │
       ├────────────────────────┐
       │                        │
       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│ Content RAG     │    │ Style RAG        │
│ - Retrieve facts│    │ - Retrieve       │
│ - Get calc data │    │   examples       │
│ - Find refs     │    │ - Get templates  │
└────────┬────────┘    └────────┬─────────┘
```

**Desktop Agent Sync Loop (high level)**  
- Watch designated folders → detect new/updated files → create artifact/version IDs → upload originals to object store → update metadata DB → re-index content/style collections.  
- Desktop execution: resolve artifact/version → open exact file in Word/Excel/Revit → maintain bidirectional updates with server indexes.

### Smart Chunker and Style Exemplar Filtering

```python
def classify_chunk_type(chunk, metadata):
    """
    Determine if chunk is content (factual) or style (curated exemplar).

    Content chunks:
    - Calculations, results, data, specifications

    Style chunks (CURATED EXEMPLARS ONLY):
    - Section templates (how we write introductions)
    - Approved boilerplate paragraphs
    - Narrative transition patterns
    - Standard phrase banks
    - Methodology description templates

    NOT style chunks:
    - One-off narrative paragraphs
    - Ad-hoc explanations
    - Generic filler text
    """
```

Style Chunk Criteria  
✅ Section appears in 3+ documents with 85%+ similarity  
✅ Explicitly marked as "template" or "standard language"  
✅ User-pinned as exemplar  
✅ High quality score (>0.8 for grammar/completeness/clarity)  
❌ Project-specific one-offs or filler text  

Add a `StyleExemplarFilter` that enforces these rules before writing to `style_{company_id}`.

### Query Analyzer (Structured Outputs)

```python
class QueryAnalyzer:
    """
    Parse user requests into structured parameters for template selection and retrieval framing.
    """

    def analyze_query(self, user_request: str) -> dict:
        return {
            "doc_type": "...",              # calculation_narrative | design_report | method_statement
            "section_type": "...",          # assumptions | methodology | results | limitations
            "engineering_function": "...",  # justify_design | summarize_analysis | report_pass_fail | cite_codes
            "constraints": {
                "code_references": ["ACI 318-19"],
                "project_context": "...",
                "required_sections": [],
                "calculation_type": "structural",
            },
        }
```

Query Analyzer Output feeds:  
- `doc_type` → template selection  
- `section_type` → structure definition  
- `engineering_function` → RAG query framing  
- `constraints` → metadata filters (codes, calculation_type, project context)

### Phase-by-Phase Implementation
- **Phase 1-2**: RAG + template matching + voice profile rules (production-ready without training)
- **Phase 3+**: Optional LoRA fine-tuning (only if RAG quality < 80% or voice matching insufficient)

### Technology Stack: Style Learning Strategy (Tiered)
- Tier 1: RAG retrieval of style exemplars (immediate, no training)
- Tier 2: Template matching + voice rules (deterministic patterns)
- Tier 3+: Optional LoRA adapters (train only if needed, per-company or per-voice-family)
  - IMPORTANT: System is production-ready after Tier 2; fine-tuning is an optimization.

### Local Model Decision Tree
- Use cloud (OpenAI/Anthropic): default, highest quality.
- Use local models when:
  - Company prohibits cloud API calls (data residency).
  - Cost > $10k/month (self-hosting ROI positive).
  - Latency < 200ms required (cannot tolerate API round-trip).
- Local deployment requires: 2x NVIDIA A100 80GB, vLLM/TGI, and added ops complexity.

### Desktop Agent Architecture (Execution + Sync Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Agent Layer                           │
├─────────────────────┬───────────────────────────────────────────┤
│  Sync Engine        │  Execution Engine                         │
│  • File watcher     │  • Open exact version in Word             │
│  • Change detector  │  • Apply AI edits to local docs           │
│  • Version creator  │  • Execute embedded calculations          │
│  • Upload/download  │  • Launch Office automation               │
│  • Conflict handler │                                           │
│                     │  Platform Integrations:                   │
│  Sync Loop:         │  • Windows: COM automation (.NET bridge)  │
│  1. Watch folders   │  • macOS: AppleScript/JXA                 │
│  2. Detect changes  │  • Linux: LibreOffice UNO                 │
│  3. Create version  │                                           │
│  4. Upload to cloud │                                           │
│  5. Update index    │                                           │
└─────────────────────┴───────────────────────────────────────────┘
                              ↕
                    (Bidirectional sync)
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      Cloud Services                              │
│  API Gateway → Ingest/Retrieval/Generation → Storage            │
└─────────────────────────────────────────────────────────────────┘
```

Desktop Agent Responsibilities  
✅ Monitor local folders, generate artifact_id/version_id on save  
✅ Upload/download versions with metadata and conflict detection  
✅ Open specific document versions in native apps  
✅ Allow offline work (queue sync when online)  
❌ No document parsing, embedding generation, or LLM generation (done in cloud)

### Developer Tools Naming
- Use **Developer CLI** / **Automation CLI** for batch ingestion, template ops, and re-indexing; keep out of the core product surface.

### Schema Versioning
- Add `schema_version: "1.0"` to data models (DocumentMetadata, ChunkMetadata, Template) for migration tracking.

### Out of Scope (Explicit)
- ❌ Real-time collaborative editing (use Office 365)
- ❌ Project management features
- ❌ CAD/Revit file parsing (beyond metadata stubs)
- ❌ Email integration (unless explicitly requested)
- ❌ Mobile apps (desktop + web only)
