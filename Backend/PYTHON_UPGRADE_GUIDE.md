# Python Upgrade Guide

## Current Status
- **Current Python Version**: 3.10.6
- **Required Python Version**: 3.11+ (for LangGraph streaming support)

## Why Upgrade?
Python 3.11+ is required for proper async streaming support with LangGraph. The `get_stream_writer()` function works correctly in async nodes starting with Python 3.11.

## How to Upgrade Python on Windows

### Option 1: Download from python.org (Recommended)
1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 (latest stable version)
3. Run the installer
4. **Important**: Check "Add Python to PATH" during installation
5. After installation, verify:
   ```powershell
   python --version
   # Should show: Python 3.11.x or Python 3.12.x
   ```

### Option 2: Using pyenv-win (If you need multiple Python versions)
1. Install pyenv-win:
   ```powershell
   git clone https://github.com/pyenv-win/pyenv-win.git $HOME\.pyenv
   ```
2. Set environment variables in PowerShell:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv","User")
   [System.Environment]::SetEnvironmentVariable('PYENV_ROOT',$env:USERPROFILE + "\.pyenv","User")
   [System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv","User")
   ```
3. Install Python 3.11+:
   ```powershell
   pyenv install 3.11.9
   pyenv global 3.11.9
   ```

## After Upgrading

### 1. Recreate Virtual Environment
```powershell
cd Backend
# Remove old venv (optional, but recommended)
Remove-Item -Recurse -Force venv

# Create new venv with Python 3.11+
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Verify Python version in venv
python --version

# Reinstall dependencies
pip install -r ..\requirements\python\Backend\requirements.txt
```

### 2. Verify Streaming Works
After upgrading, test the streaming endpoint:
```powershell
# Start the server
python api_server.py

# In another terminal, test streaming
# (Use your frontend or curl/Postman to test /chat/stream endpoint)
```

### 3. Update IDE/Editor
If you're using VS Code or PyCharm:
- **VS Code**: Update Python interpreter path (Ctrl+Shift+P → "Python: Select Interpreter")
- **PyCharm**: File → Settings → Project → Python Interpreter → Select Python 3.11+

## Troubleshooting

### "Python not found" after installation
- Make sure Python was added to PATH during installation
- Restart your terminal/IDE after installation
- Manually add Python to PATH if needed:
  - Add `C:\Users\<YourName>\AppData\Local\Programs\Python\Python3.11\` to PATH
  - Add `C:\Users\<YourName>\AppData\Local\Programs\Python\Python3.11\Scripts\` to PATH

### Multiple Python versions
If you have multiple Python versions:
```powershell
# Check all Python versions
py -3.10 --version
py -3.11 --version
py -3.12 --version

# Use specific version for venv
py -3.11 -m venv venv
```

### Virtual environment issues
If the virtual environment doesn't activate:
```powershell
# PowerShell execution policy might block scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again
.\venv\Scripts\Activate.ps1
```

## Benefits of Python 3.11+
- ✅ Proper async streaming support with LangGraph
- ✅ Better performance (10-60% faster than 3.10)
- ✅ Better error messages
- ✅ Exception groups and except* syntax
- ✅ TaskGroups for structured concurrency

## Questions?
If you encounter any issues during the upgrade, check:
1. Python version: `python --version`
2. Virtual environment Python: `.\venv\Scripts\python.exe --version`
3. LangGraph version: `pip show langgraph`


