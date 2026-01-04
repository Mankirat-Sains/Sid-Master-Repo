# Root Virtual Environment Setup

This guide explains how to set up and use the root virtual environment for the entire repository.

## Quick Setup

### macOS/Linux
```bash
chmod +x setup_root_venv.sh
./setup_root_venv.sh
```

### Windows
```cmd
setup_root_venv.bat
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install common dependencies (optional)
pip install -r requirements/consolidated/python-unique-requirements.txt
```

## Usage

### Activating the Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

### Installing Dependencies

The root venv can be used for:
1. **Common development tools** (shared across projects)
2. **Testing dependencies** that are used across multiple projects
3. **Development utilities** (black, pytest, mypy, etc.)

**Recommended approach:**
- Install only **shared/common** dependencies in the root venv
- Keep **project-specific** dependencies in their own venvs
- Use root venv for development tools and utilities

### Example: Installing Development Tools

```bash
# Activate root venv
source venv/bin/activate

# Install common development tools
pip install black pytest mypy flake8 ipython jupyter

# Install project-specific dependencies in their own venvs
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements/python/Backend/requirements.txt
```

## Recommended Structure

```
Sid-Master-Repo/
├── venv/                    # Root venv (shared dev tools)
├── Backend/
│   └── venv/                # Backend-specific dependencies
├── Frontend/backend/
│   └── venv/                # Frontend backend dependencies
└── Local Agent/ExcelAgent/AI/
    └── venv/                # Excel Agent dependencies
```

## What to Install in Root Venv

✅ **Do install:**
- Development tools (black, pytest, mypy, flake8)
- Code quality tools (pre-commit, ruff)
- Testing frameworks (pytest, unittest)
- Documentation tools (sphinx, mkdocs)
- Jupyter/IPython for interactive development
- Common utilities used across projects

❌ **Don't install:**
- Project-specific dependencies (FastAPI, LangChain, etc.)
- Conflicting versions of packages
- Heavy ML libraries (unless used across multiple projects)

## Deactivating

When you're done working:
```bash
deactivate
```

## Troubleshooting

### Virtual environment not activating
- Make sure you're in the repository root directory
- Check that `venv/bin/activate` (or `venv\Scripts\activate`) exists
- Verify Python is installed: `python3 --version`

### Permission errors
- On macOS/Linux, you may need: `chmod +x venv/bin/activate`
- On Windows, run Command Prompt as Administrator if needed

### Path issues
- If you see "command not found", make sure the venv is activated
- Check that Python is in your PATH

## Best Practices

1. **Always activate** the root venv before running shared development tools
2. **Keep it clean** - only install truly shared dependencies
3. **Document** what's installed in the root venv (update this file)
4. **Use project venvs** for project-specific work
5. **Update regularly** - `pip install --upgrade pip` periodically

## Current Root Venv Dependencies

To see what's currently installed:
```bash
source venv/bin/activate
pip list
```

To export current dependencies:
```bash
pip freeze > requirements/ROOT_VENV_REQUIREMENTS.txt
```


