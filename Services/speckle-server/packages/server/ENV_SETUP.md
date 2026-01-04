# Environment Variables Setup Guide

## Where to Put .env Files

You need to create `.env` files in **two different locations**:

### 1. AI Service `.env` File

**Location:** `packages/ai-service/.env`

**Contents:**

```bash
API_KEY=your-secret-api-key-here
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=*
```

**Important:** The AI service uses `pydantic-settings` which automatically loads from `.env` in the current working directory.

### 2. Server `.env` File

**Location:** `packages/server/.env`

**Contents:**

```bash
# Add these lines to your existing server .env file
AI_SERVICE_ORIGIN=http://localhost:8001
AI_SERVICE_API_KEY=your-secret-api-key-here
```

**Important:**

- The server uses `dotenv` and loads from `packages/server/.env` (see `bootstrap.js` line 48)
- Use the **same API key** value in both files for authentication to work
- Add these variables to your existing server `.env` file if you already have one

## Quick Setup Commands

### Windows (PowerShell):

**1. Create AI Service .env:**

```powershell
cd packages\ai-service
@"
API_KEY=test-api-key-123
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=*
"@ | Out-File -FilePath .env -Encoding utf8
```

**2. Add to Server .env:**

```powershell
cd packages\server
Add-Content -Path .env -Value "`nAI_SERVICE_ORIGIN=http://localhost:8001`nAI_SERVICE_API_KEY=test-api-key-123"
```

### Linux/Mac:

**1. Create AI Service .env:**

```bash
cd packages/ai-service
cat > .env << EOF
API_KEY=test-api-key-123
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=*
EOF
```

**2. Add to Server .env:**

```bash
cd packages/server
echo "" >> .env
echo "AI_SERVICE_ORIGIN=http://localhost:8001" >> .env
echo "AI_SERVICE_API_KEY=test-api-key-123" >> .env
```

## Verify Configuration

After creating the files, verify they're in the right place:

```bash
# Check AI service .env exists
ls packages/ai-service/.env

# Check server .env contains the new variables
grep AI_SERVICE packages/server/.env
```

## Security Notes

⚠️ **Important Security Practices:**

1. **Never commit `.env` files to git** - They should be in `.gitignore`
2. **Use strong, unique API keys** in production - Don't use `test-api-key-123`
3. **Keep API keys synchronized** - Both services must use the same `AI_SERVICE_API_KEY` value
4. **Use different keys for different environments** - Dev, staging, production should have different keys

## Environment Variable Reference

### AI Service (`packages/ai-service/.env`):

- `API_KEY` - Secret key for authenticating requests from the server
- `PORT` - Port the AI service listens on (default: 8001)
- `HOST` - Host to bind to (default: 0.0.0.0)
- `CORS_ORIGINS` - CORS allowed origins (default: \*)

### Server (`packages/server/.env`):

- `AI_SERVICE_ORIGIN` - Full URL of the AI service (e.g., `http://localhost:8001`)
- `AI_SERVICE_API_KEY` - Must match the `API_KEY` in the AI service `.env`

## Troubleshooting

**AI Service can't read API_KEY:**

- Make sure `.env` is in `packages/ai-service/` directory
- Check file permissions
- Verify the file is named exactly `.env` (not `.env.txt`)

**Server can't connect to AI Service:**

- Check `AI_SERVICE_ORIGIN` matches where AI service is running
- Verify `AI_SERVICE_API_KEY` matches `API_KEY` in AI service `.env`
- Restart the server after adding environment variables

**Authentication fails:**

- Ensure both services use the **exact same** API key value
- Check for extra spaces or newlines in the `.env` files
- Restart both services after changing API keys

