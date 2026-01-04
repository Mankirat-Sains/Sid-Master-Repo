# test_imports.py
print("1. Starting...")
import os
print("2. os imported")
from dotenv import load_dotenv
print("3. dotenv imported")
load_dotenv()
print("4. .env loaded")
print("5. OPENAI_API_KEY:", "Found" if os.getenv("OPENAI_API_KEY") else "NOT FOUND")
print("6. SUPABASE_URL:", "Found" if os.getenv("SUPABASE_URL") else "NOT FOUND")

print("7. Importing main...")
from main import run_agentic_rag
print("8. main imported successfully!")