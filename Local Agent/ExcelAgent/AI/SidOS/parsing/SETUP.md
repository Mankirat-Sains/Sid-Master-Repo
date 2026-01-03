# Setup Guide for Parsing Directory

## Everything Required to Run Parsing Scripts

### 1. Python Version
- **Python 3.8+** (you have 3.13.2 ✓)

### 2. Install Dependencies

From the `parsing` directory, run:

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS/parsing"
pip install -r requirements.txt
```

This installs:
- `openpyxl>=3.1.0` - For reading Excel files
- `openai>=1.0.0` - For AI-driven understanding
- `python-dotenv>=1.0.0` - For environment variables

### 3. Set OpenAI API Key

The parser requires an OpenAI API key for AI features. You have two options:

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Option B: .env File**
Create a `.env` file in the `trainexcel` root directory:
```
OPENAI_API_KEY=your-api-key-here
```

**Option C: Command Line Flag**
```bash
python parse_workbook.py "file.xlsx" --api-key "your-api-key-here"
```

### 4. Verify Installation

Test that everything works:

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS/parsing"
python -c "import openpyxl; import openai; from dotenv import load_dotenv; print('All dependencies installed!')"
```

### 5. Run the Parser

```bash
python parse_workbook.py "path/to/your/workbook.xlsx" -o "output_metadata.json"
```

## Complete Setup Commands (Copy & Paste)

```bash
# Navigate to parsing directory
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS/parsing"

# Install dependencies
pip install -r requirements.txt

# Set API key (replace with your actual key)
export OPENAI_API_KEY="sk-..."

# Test installation
python -c "import openpyxl; import openai; print('Setup complete!')"

# Run parser on your Excel file
python parse_workbook.py "/path/to/your/file.xlsx" -o "metadata.json"
```

## What Each Dependency Does

- **openpyxl**: Reads Excel files (.xlsx), extracts cell values, formulas, colors, etc.
- **openai**: AI analyzes the workbook structure, finds legends, understands cell meanings
- **python-dotenv**: Loads environment variables from .env file

## Troubleshooting

**"No module named 'openpyxl'"**
→ Run: `pip install -r requirements.txt`

**"OpenAI API key not set"**
→ Set `OPENAI_API_KEY` environment variable or use `--api-key` flag

**"Import errors"**
→ Make sure you're in the venv: `source venv/bin/activate` (or however you activate your venv)

## Cost & Time Estimates

- **Cost**: ~$0.10-0.50 per workbook (OpenAI API calls)
- **Time**: ~2-5 minutes per workbook (depends on workbook size and AI processing)


