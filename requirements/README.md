# Requirements Directory

This directory contains all dependency files and requirements for the entire Sid-Master-Repo project.

## Structure

```
requirements/
├── python/              # Python requirements.txt files organized by project
├── nodejs/              # Node.js package.json files organized by project
├── docker/              # Dockerfiles and containerization configs
├── consolidated/        # Merged/consolidated dependency files
└── README.md           # This file
```

## Python Projects

### Backend Services
- `python/Backend/requirements.txt` - Main Backend RAG system dependencies
- `python/Frontend-backend/requirements.txt` - Frontend backend API server

### Local Agents
- `python/Local-Agent-ExcelAgent-AI/requirements.txt` - Excel Agent main dependencies
- `python/Local-Agent-ExcelAgent-AI-backend/requirements.txt` - Excel Agent backend
- `python/Local-Agent-ExcelAgent-AI-SidOS/requirements.txt` - Excel Agent SidOS module
- `python/Local-Agent-ExcelAgent-AI-SidOS-parsing/requirements.txt` - Excel Agent parsing module
- `python/Local-Agent-dataprocessing-florence/requirements.txt` - Florence embedding model
- `python/Local-Agent-dataprocessing-florence-imageCHAT/requirements.txt` - Image chat module

### Sandbox Projects
- `python/sandbox-GraphQL-MCP-fact-engine/requirements.txt` - GraphQL MCP fact engine service

## Node.js Projects

- `nodejs/Frontend-Frontend/package.json` - Main Nuxt.js frontend application
- `nodejs/Local-Agent-ExcelAgent-AI/package.json` - Excel Agent Office Add-in

## Docker

- `docker/sandbox-GraphQL-MCP/Dockerfile` - GraphQL MCP service containerization

## Consolidated Files

- `consolidated/python-all-requirements.txt` - All Python dependencies merged (may have conflicts)
- `consolidated/python-unique-requirements.txt` - Unique Python packages across all projects
- `consolidated/nodejs-all-dependencies.txt` - All Node.js dependencies listed

## Installation Instructions

### Python Projects

Each Python project should be installed separately:

```bash
# Example: Install Frontend backend dependencies
cd Frontend/backend
pip install -r ../../requirements/python/Frontend-backend/requirements.txt

# Example: Install Backend dependencies
cd Backend
pip install -r ../requirements/python/Backend/requirements.txt
```

### Node.js Projects

```bash
# Example: Install Frontend dependencies
cd Frontend/Frontend
npm install  # Uses local package.json, or copy from requirements/nodejs/
```

## Notes

- Some projects may have overlapping dependencies with different version requirements
- Always check individual project requirements.txt files for specific version constraints
- Use virtual environments for Python projects to avoid conflicts
- The consolidated files are for reference only - use individual project files for installation


