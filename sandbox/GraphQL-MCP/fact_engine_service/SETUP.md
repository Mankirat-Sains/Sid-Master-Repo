# Fact Engine Service - Setup Guide

## Quick Start

1. **Install Dependencies**
```bash
cd fact_engine_service
pip install -r requirements.txt
```

2. **Configure Environment**

Create a `.env` file in the `fact_engine_service` directory:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=speckle
DB_USER=postgres
DB_PASSWORD=your_password

# GraphQL Configuration (optional)
GRAPHQL_ENDPOINT=http://localhost:4000/graphql
GRAPHQL_AUTH_TOKEN=your_token_here
GRAPHQL_USE_MCP=false

# LLM Configuration (required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
PLANNER_TEMPERATURE=0.1
COMPOSER_TEMPERATURE=0.3

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
LOG_LEVEL=INFO
```

3. **Run the Service**

```bash
# From the fact_engine_service directory
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Test the Service**

```bash
# Health check
curl http://localhost:8000/health

# Query example
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Do we have any timber columns?"}'
```

## GraphQL Connection

The service can connect to Speckle via GraphQL in two ways:

1. **Direct GraphQL** (default): Uses HTTP client to query GraphQL endpoint
2. **GraphQL MCP**: Uses the GraphQL MCP server from the parent directory

To use GraphQL MCP:
- Set `GRAPHQL_USE_MCP=true` in your `.env`
- Ensure the GraphQL MCP server is built in the parent directory
- The service will automatically use the MCP client if available

## Architecture

The service follows a three-phase architecture:

1. **Semantic Planner**: Converts NL questions → FactPlans (JSON)
2. **Fact Executor**: Executes FactPlans → Extracted Facts
3. **Answer Composer**: Synthesizes Facts → Human-readable Answers

## Adding New Extractors

To add a new fact extractor:

1. Create a new file in `extractors/` (e.g., `extractors/custom_fact.py`)
2. Inherit from `FactExtractor` base class
3. Implement required methods
4. Register in `executor/registry.py`

Example:
```python
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence

class CustomFactExtractor(FactExtractor):
    @property
    def fact_name(self) -> str:
        return "custom_fact"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "custom_fact"
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        # Your extraction logic here
        return FactValue(value="...", confidence=0.9, evidence=[])
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check with component status
- `POST /query` - Answer a natural language question
- `GET /facts` - List available fact types

## Troubleshooting

**Import Errors**: Make sure you're running from the `fact_engine_service` directory or have it in your Python path.

**Database Connection**: Verify your database credentials and that PostgreSQL is running.

**GraphQL Connection**: Check that the GraphQL endpoint is accessible and authentication is configured correctly.

**LLM Errors**: Ensure your OpenAI API key is valid and you have sufficient credits.


