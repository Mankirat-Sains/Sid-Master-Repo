# Requirements Index

This file maps each requirements file in this directory to its original location in the repository.

## Python Requirements Files

| Requirements File | Original Location | Description |
|------------------|-------------------|-------------|
| `python/Backend/requirements.txt` | `Backend/` (inferred) | Main Backend RAG system - LangChain, FastAPI, Supabase |
| `python/Frontend-backend/requirements.txt` | `Frontend/backend/requirements.txt` | Frontend backend API server |
| `python/Local-Agent-ExcelAgent-AI/requirements.txt` | `Local Agent/ExcelAgent/AI/requirements.txt` | Excel Agent main dependencies |
| `python/Local-Agent-ExcelAgent-AI-backend/requirements.txt` | `Local Agent/ExcelAgent/AI/backend/requirements.txt` | Excel Agent backend server |
| `python/Local-Agent-ExcelAgent-AI-SidOS/requirements.txt` | `Local Agent/ExcelAgent/AI/SidOS/requirements.txt` | Excel Agent SidOS module |
| `python/Local-Agent-ExcelAgent-AI-SidOS-parsing/requirements.txt` | `Local Agent/ExcelAgent/AI/SidOS/parsing/requirements.txt` | Excel Agent parsing module |
| `python/Local-Agent-dataprocessing-florence/requirements.txt` | `Local Agent/dataprocessing/florence_embedding/requirements.txt` | Florence embedding model |
| `python/Local-Agent-dataprocessing-florence-imageCHAT/requirements.txt` | `Local Agent/dataprocessing/florence_embedding/imageCHAT/requirements.txt` | Image chat module |

## Node.js Package Files

| Package File | Original Location | Description |
|--------------|------------------|-------------|
| `nodejs/Frontend-Frontend/package.json` | `Frontend/Frontend/package.json` | Nuxt.js frontend application |
| `nodejs/Local-Agent-ExcelAgent-AI/package.json` | `Local Agent/ExcelAgent/AI/package.json` | Excel Office Add-in (webpack, TypeScript) |

## Docker Files

| Docker File | Original Location | Description |
|-------------|------------------|-------------|
| `docker/sandbox-GraphQL-MCP/Dockerfile` | `sandbox/GraphQL-MCP/Dockerfile` | Bun-based containerization for GraphQL MCP |

## Consolidated Files

| File | Description |
|-----|-------------|
| `consolidated/python-all-requirements.txt` | All Python dependencies from all projects (may have conflicts) |
| `consolidated/python-unique-requirements.txt` | Unique Python packages with highest version requirements |
| `consolidated/nodejs-all-dependencies.txt` | All Node.js dependencies listed by project |
| `consolidated/INSTALLATION_GUIDE.md` | Comprehensive installation guide for all projects |

## Usage

1. **For installation**: Use the original requirements files in each project directory, or copy from the corresponding file in this requirements folder.

2. **For reference**: Use consolidated files to see all dependencies across the repository.

3. **For new projects**: Check existing requirements files to see what dependencies are already used in the repository.

## Notes

- The `Backend/requirements.txt` file is inferred from codebase imports - verify actual dependencies before use
- Some requirements files may have version conflicts - always use project-specific files for installation
- Docker files are included for containerization reference


