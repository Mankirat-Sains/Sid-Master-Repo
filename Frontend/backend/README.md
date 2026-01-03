# SidOS Backend API

Simple FastAPI backend for SidOS Word export functionality.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## Endpoints

### GET `/`
Health check endpoint

### GET `/health`
Returns API status and library availability

### POST `/export/word`
Exports HTML content to a Word document

**Request Body:**
```json
{
  "content": "<h1>Title</h1><p>Content here...</p>",
  "file_name": "Proposal.docx"
}
```

**Response:**
Returns a downloadable Word document file

## Environment Variables

The server uses the default port 8000. You can override this by setting the `PORT` environment variable.


