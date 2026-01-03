# Fact Engine Service

## Core Principle

**We do not answer questions directly.**
**We extract facts.**
**Questions are compositions of facts.**

This principle is what makes the system adaptable.

## Architecture

```
User Question
   ↓
(1) Semantic Planner  ← LLM (JSON only)
   ↓
Fact Plan (structured)
   ↓
(2) Fact Engine (deterministic Python)
   ↓
Extracted Facts (structured)
   ↓
(3) Answer Composer ← LLM (reasoning + explanation)
   ↓
Final Answer + Evidence
```

## How It Works

1. **Semantic Planner**: Converts natural language questions into structured FactPlans (JSON only, no SQL)
2. **Fact Engine**: Executes FactPlans using deterministic extractors that operate on Speckle data
3. **Answer Composer**: Synthesizes extracted facts into human-readable answers with confidence scores

## Key Features

- ✅ **Connector-agnostic**: Works with any Speckle data source (Postgres, GraphQL)
- ✅ **Auditable**: Every fact includes confidence and evidence
- ✅ **Deterministic**: Extractors produce consistent results
- ✅ **Composable**: New questions reuse existing extractors
- ✅ **GraphQL Support**: Can query Speckle via GraphQL API

## Setup

1. Install dependencies:
```bash
pip install fastapi uvicorn pydantic psycopg2-binary asyncpg openai python-dotenv
```

2. Configure environment variables (see `config.py`)

3. Run the service:
```bash
uvicorn main:app --reload
```

## Usage

POST `/query` with:
```json
{
  "question": "Do we have any timber columns in our projects?"
}
```

## Extending the System

To add new capabilities:
- Add a new **extractor** when you need a new fact type
- Most questions reuse existing extractors through composition


