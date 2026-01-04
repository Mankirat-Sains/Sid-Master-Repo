# Installation Guide for Sid-Master-Repo

This guide provides instructions for installing dependencies for all projects in the repository.

## Overview

The repository contains multiple projects with different dependency requirements:
- **Backend**: Python FastAPI RAG system
- **Frontend**: Nuxt.js Vue application
- **Frontend Backend**: Python FastAPI server for frontend
- **Excel Agent**: Python Excel automation + Office Add-in (Node.js)
- **Florence Embedding**: Python ML model for embeddings
- **GraphQL MCP**: Python FastAPI service

## Python Projects

### Prerequisites
- Python 3.8+ (Python 3.10+ recommended)
- pip (Python package manager)
- Virtual environment tool (venv, conda, or virtualenv)

### Installation Steps

#### 1. Backend RAG System
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements/python/Backend/requirements.txt
```

#### 2. Frontend Backend API
```bash
cd Frontend/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../../requirements/python/Frontend-backend/requirements.txt
```

#### 3. Excel Agent - Main
```bash
cd "Local Agent/ExcelAgent/AI"
python -m venv venv
source venv/bin/activate
pip install -r ../../../requirements/python/Local-Agent-ExcelAgent-AI/requirements.txt
```

#### 4. Excel Agent - Backend
```bash
cd "Local Agent/ExcelAgent/AI/backend"
python -m venv venv
source venv/bin/activate
pip install -r ../../../../requirements/python/Local-Agent-ExcelAgent-AI-backend/requirements.txt
```

#### 5. Excel Agent - SidOS
```bash
cd "Local Agent/ExcelAgent/AI/SidOS"
python -m venv venv
source venv/bin/activate
pip install -r ../../../../requirements/python/Local-Agent-ExcelAgent-AI-SidOS/requirements.txt
```

#### 6. Excel Agent - SidOS Parsing
```bash
cd "Local Agent/ExcelAgent/AI/SidOS/parsing"
python -m venv venv
source venv/bin/activate
pip install -r ../../../../../requirements/python/Local-Agent-ExcelAgent-AI-SidOS-parsing/requirements.txt
```

#### 7. Florence Embedding Model
```bash
cd "Local Agent/dataprocessing/florence_embedding"
python -m venv venv
source venv/bin/activate
pip install -r ../../../requirements/python/Local-Agent-dataprocessing-florence/requirements.txt
```

#### 8. GraphQL MCP Fact Engine
```bash
cd sandbox/GraphQL-MCP/fact_engine_service
python -m venv venv
source venv/bin/activate
pip install -r ../../../requirements/python/sandbox-GraphQL-MCP-fact-engine/requirements.txt
```

## Node.js Projects

### Prerequisites
- Node.js 18+ (Node.js 20+ recommended)
- npm or yarn

### Installation Steps

#### 1. Frontend (Nuxt.js)
```bash
cd Frontend/Frontend
npm install
# Or copy package.json from requirements/nodejs/Frontend-Frontend/package.json
```

#### 2. Excel Agent Office Add-in
```bash
cd "Local Agent/ExcelAgent/AI"
npm install
# Or copy package.json from requirements/nodejs/Local-Agent-ExcelAgent-AI/package.json
```

## Environment Variables

Most projects require environment variables. Create a `.env` file in the project root or parent directory with:

```env
# OpenAI API (required for most projects)
OPENAI_API_KEY=your_openai_api_key

# Supabase (required for Backend and Florence)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Anthropic (optional, for Claude models)
ANTHROPIC_API_KEY=your_anthropic_key

# Server Configuration
PORT=8000
```

## Quick Install Script

You can create a script to install all dependencies:

```bash
#!/bin/bash
# install-all.sh

# Python projects
for dir in Backend "Frontend/backend" "Local Agent/ExcelAgent/AI" "Local Agent/ExcelAgent/AI/backend" "Local Agent/dataprocessing/florence_embedding" "sandbox/GraphQL-MCP/fact_engine_service"; do
    echo "Installing Python dependencies for $dir..."
    cd "$dir"
    python -m venv venv
    source venv/bin/activate
    pip install -r ../../requirements/python/$(echo $dir | tr '/' '-')/requirements.txt
    deactivate
    cd ../..
done

# Node.js projects
echo "Installing Node.js dependencies for Frontend..."
cd Frontend/Frontend
npm install
cd ../..

echo "Installing Node.js dependencies for Excel Agent..."
cd "Local Agent/ExcelAgent/AI"
npm install
cd ../..
```

## Troubleshooting

### Python Version Conflicts
- Use virtual environments for each project
- Some projects may require specific Python versions
- Check individual requirements.txt for version constraints

### Node.js Version Conflicts
- Use nvm (Node Version Manager) to switch between Node versions
- Each project may require different Node.js versions

### Missing Dependencies
- Check if all requirements.txt files are present
- Verify environment variables are set
- Some dependencies may need system-level packages (e.g., PostgreSQL client libraries)

### Permission Errors
- Use `pip install --user` for user-level installation
- On Linux/Mac, may need `sudo` for system packages
- Consider using virtual environments to avoid permission issues

## Notes

- **Do NOT** install all Python dependencies in one environment - use separate virtual environments
- **Do NOT** use the consolidated requirements files for installation - they are for reference only
- Always check individual project README files for specific setup instructions
- Some projects may have additional setup steps beyond dependency installation


