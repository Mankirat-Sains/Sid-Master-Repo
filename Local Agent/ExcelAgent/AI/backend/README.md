# Mantle Excel Backend

Intelligent backend server for the Mantle Excel Add-in.

## Features

- **Intelligent Command Processing**: Natural language understanding using OpenAI
- **Engineering Calculations**: Beam, column, and structural analysis
- **Building Code Validation**: AS3600, CSA, Eurocode support
- **Structured Responses**: Returns Excel-specific actions for the add-in to execute
- **Real-time Processing**: Fast API responses for smooth user experience

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
PORT=8000
```

### 3. Run the Server

```bash
python api_server.py
```

Server will start at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

### Excel Command Processing
```
POST /api/excel/command

Body:
{
  "command": "Calculate beam moment for 15m span with 5.5 kN/m load",
  "context": {
    "workbookName": "Beam Design.xlsx",
    "sheetName": "Calculations",
    "selectedRange": {...},
    "usedRange": {...},
    "timestamp": "2025-10-29T12:00:00"
  },
  "capabilities": ["write_cells", "calculate", "validate"]
}

Response:
{
  "action": "update_multiple",
  "updates": [
    {"address": "D5", "value": 154.69, "formula": "wL²/8"},
    {"address": "D6", "value": 41.25, "formula": "wL/2"}
  ],
  "message": "Calculated beam forces",
  "reasoning": "Used standard formulas for uniformly distributed load",
  "calculations": [...],
  "validations": [...]
}
```

## Architecture

```
Excel Add-in → FastAPI Server → Orchestrator → Building Codes
                                    ↓
                            Engineering Calculations
```

### Components

1. **api_server.py**: FastAPI server with CORS enabled for Excel Add-in
2. **agents/orchestrator.py**: Intelligent command processor using OpenAI
3. **agents/building_codes.py**: Building code validation (AS3600, CSA, Eurocode)

## Supported Commands

### Calculations
- "Calculate beam moment for 15m span"
- "Design a beam with 30 MPa concrete"
- "Find shear force for 5.5 kN/m load"

### Updates
- "Update span to 15m"
- "Set concrete strength to 40 MPa"
- "Change load to 6 kN/m"

### Validation
- "Check beam design against AS3600"
- "Validate deflection limits"
- "Verify concrete strength requirements"

## Building Codes

Currently supported:
- **AS3600:2018** - Australian Concrete Structures Code
- **CSA A23.3** - Canadian Concrete Code (partial)
- **Eurocode 2** - European Concrete Code (partial)

### Validation Features

- Concrete strength requirements
- Deflection limits (L/250, L/300, etc.)
- Minimum reinforcement ratios
- Cover requirements
- Capacity checks (moment, shear)

## Development

### Adding New Calculations

Edit `agents/orchestrator.py`:

```python
def calculate_new_element(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # Your calculation logic
    return {
        "action": "update_multiple",
        "updates": [...],
        "message": "...",
        "calculations": [...]
    }
```

### Adding New Building Codes

Edit `agents/building_codes.py`:

```python
NEW_CODE_RULES = {
    "concrete_strength": {
        "min_structural": 20,
        ...
    }
}
```

## Testing

Test the server:

```bash
curl http://localhost:8000/health
```

Test Excel command:

```bash
curl -X POST http://localhost:8000/api/excel/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Calculate moment for 15m beam",
    "context": {...},
    "capabilities": ["write_cells"]
  }'
```

## Deployment

The backend can be deployed to:
- Local server (development)
- Cloud platforms (Heroku, AWS, Azure, Google Cloud)
- Docker container

For production, update the Excel Add-in config to point to your deployed URL.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes (for AI) |
| `PORT` | Server port (default: 8000) | No |
| `DEBUG` | Enable debug logging | No |

## Troubleshooting

### Server won't start
- Check if port 8000 is available
- Verify Python version (3.8+)
- Check dependencies are installed

### AI not working
- Verify OPENAI_API_KEY is set
- Check OpenAI API quota/credits
- Server will fallback to keyword matching if AI unavailable

### Excel Add-in can't connect
- Verify server is running (`/health` endpoint)
- Check CORS is enabled (should be by default)
- Verify Add-in config has correct backend URL

## License

Part of the Mantle Excel Add-in system.

