# System Architecture – Agentic Engineering Platform

## Purpose of this Document

This document is the **authoritative architectural reference** for this repository.

All code written in this repo MUST:
- Follow the architecture described here
- Respect component boundaries
- Use the defined data flows
- Avoid introducing new patterns without justification

This file exists to guide **Cursor agents and human developers** when adding or modifying components.

---

## High-Level Overview

This system is a **multi-agent, orchestrated AI platform** designed for structural / civil engineering workflows.

Core properties:
- Task-oriented orchestration (not single-pass RAG)
- Multiple specialized agents and tools
- Strong verification and human-in-the-loop support
- Continuous knowledge and ontology growth
- Separation of reasoning, execution, and retrieval

---

## Entry Point

### Web UI (Frontend)

Responsibilities:
- Accept user natural-language queries
- Display responses in chat and main viewer
- NO business logic
- NO direct tool execution

The frontend sends **only the user query + minimal metadata** to the orchestrator.

---

## Orchestrator (Plan Node)

The orchestrator is the **central control layer**.

Responsibilities:
- Interpret user intent
- Decide which capability branch(es) to invoke
- Decompose complex tasks
- Dispatch multiple calls if needed
- Re-route on verification failure

The orchestrator DOES NOT:
- Perform calculations
- Execute desktop actions
- Query databases directly

---

## Major Capability Branches

### 1. Building Model Generator

Triggered when the user wants to:
- Create a building model
- Modify an existing model
- Define geometry via natural language

Flow:
- Router → Decide between:
  - Create from scratch
  - Modify existing model
- Model generation logic
- Verifier validates structural coherence
- Output returned to orchestrator

---

### 2. Web Calculations (WebCalcs)

Triggered when numerical analysis is required.

Available tools:
- Calculator
- SkyCiv
- Jabacus
- Web search (for reference data only)

Rules:
- Orchestrator selects tool
- Tool performs computation
- Verifier checks correctness and units
- Result returned upstream

---

### 3. Database Retrieval (Core Knowledge System)

This system uses **two complementary data stores**.

#### 3.1 Speckle DB (Graph / BIM Data)

Purpose:
- Structured BIM-derived data
- Elements, geometry, relationships

Stack:
- GraphQL
- Postgres
- Cypher-style traversal

Flow:
- Cypher Generator produces query
- Speckle DB executes
- Verifier validates results
- Answer returned

Use when:
- Query involves geometry
- IFC elements
- Structural relationships

---

#### 3.2 Supabase DB (Knowledge + RAG)

Purpose:
- Building codes
- Internal documents
- Technical drawings
- Embeddings
- User query history

Flow:
- Planner decides:
  - SQL vs embedding search
  - Which tables to access
- Retrieve relevant data
- Verifier checks relevance
- Answer returned

Supabase DB is **updated continuously** to improve future responses.

---

### 4. Desktop Agent (Execution Layer)

Triggered when tasks require **interaction with real software**.

Agents:
- Excel Agent
- Word Agent
- Revit Agent

Modes:
- Think: plan and simulate actions
- Act: execute actions

Rules:
- Desktop agents NEVER reason about intent
- They execute explicit instructions only
- All actions are logged
- High-risk actions require human verification

---

## Verification Layer (Critical)

Every major step includes a verifier.

Verifier responsibilities:
- Compare output against user intent
- Detect logical inconsistencies
- Catch hallucinations or unsafe actions
- Provide structured feedback to the planner

Verifier may:
- Approve output
- Send correction instructions upstream
- Trigger human verification

---

## Human-in-the-Loop

Used when:
- Actions modify external systems
- Risk or liability is high
- Ambiguity cannot be resolved automatically

Human verification acts as a **hard gate**, not a suggestion.

---

## Continuous Learning & Ontology Growth

The system improves over time by:
- Tracking user queries
- Tracking outputs
- Updating embeddings
- Expanding ontology relationships (e.g. beam ↔ column)

This is NOT online model training.
This is **knowledge system evolution**.

---

## Models Used (Conceptual)

This system assumes availability of:
1. Drawing information extraction model
2. Excel / Word / Revit understanding model
3. YOLO-based vision model
4. Semantic understanding model
5. Synthesis model
6. Speckle-specific reasoning model

These are modular and replaceable.

---

## Architectural Constraints (DO NOT VIOLATE)

- No monolithic agent
- No tool execution inside orchestrator
- No direct DB access from frontend
- No silent execution of desktop actions
- No skipping verification steps

If a change violates these constraints, it MUST be documented and justified.

---

## How to Use This File

When writing code:
- Refer to this document explicitly
- Match component responsibilities
- Do not invent new layers without updating this file

This document is the system contract.