# Speckle AI Service

AI integration microservice for Speckle Server with OpenAI integration for querying Speckle models using GraphQL.

## Features

- OpenAI chat integration with configurable models
- Speckle GraphQL client for fetching stream data, objects, and comments
- Context-aware responses with automatic token limit management
- BIM/AEC domain expertise built into system prompts

## Development

### Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:

- `OPENAI_API_KEY` - Your OpenAI API key
- `SPECKLE_GRAPHQL_URL` - Speckle server GraphQL endpoint (default: http://localhost:3000/graphql)
- `SPECKLE_SERVICE_TOKEN` - Service token for authenticating GraphQL requests
- `CHAT_MODEL` - OpenAI model to use (default: gpt-4o-mini)
- `MAX_TOKENS` - Maximum tokens for responses (default: 20000)
- `TEMPERATURE` - Model temperature (default: 0.7)

4. Run the service:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/v1/chat` - Chat endpoint (requires `X-API-Key` header)

### Chat Endpoint

Request body:

```json
{
  "message": "What are the recent changes in this project?",
  "project_id": "stream-id-here", // Optional: enables Speckle context fetching
  "context": {} // Optional: additional context dict
}
```

When `project_id` is provided, the service will:

1. Fetch stream metadata (name, description)
2. Retrieve recent commits (up to 5)
3. Fetch comment threads (up to 10)
4. Build context string (truncated to ~3000 tokens)
5. Send to OpenAI with BIM/AEC system prompt
6. Return response with Speckle object references

## Docker

Build and run with Docker:

```bash
docker build -t speckle-ai-service .
docker run -p 8001:8001 --env-file .env speckle-ai-service
```
