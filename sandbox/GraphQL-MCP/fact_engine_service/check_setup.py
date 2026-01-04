#!/usr/bin/env python3
"""Quick setup verification script"""
import sys
from pathlib import Path

# Add parent to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import settings

print("=" * 60)
print("Fact Engine Service - Setup Verification")
print("=" * 60)
print()

# Check GraphQL config
print("📡 GraphQL Configuration:")
if settings.GRAPHQL_ENDPOINT:
    print(f"  ✅ GRAPHQL_ENDPOINT: {settings.GRAPHQL_ENDPOINT}")
else:
    print(f"  ❌ GRAPHQL_ENDPOINT: Not set")
    print(f"     Set it in .env: GRAPHQL_ENDPOINT=http://your-endpoint/graphql")

if settings.GRAPHQL_AUTH_TOKEN:
    token_preview = settings.GRAPHQL_AUTH_TOKEN[:20] + "..." if len(settings.GRAPHQL_AUTH_TOKEN) > 20 else settings.GRAPHQL_AUTH_TOKEN
    print(f"  ✅ GRAPHQL_AUTH_TOKEN: {token_preview}")
else:
    print(f"  ⚠️  GRAPHQL_AUTH_TOKEN: Not set (may not be required)")

print()

# Check OpenAI config
print("🤖 OpenAI Configuration:")
if settings.OPENAI_API_KEY:
    key_preview = settings.OPENAI_API_KEY[:20] + "..." if len(settings.OPENAI_API_KEY) > 20 else settings.OPENAI_API_KEY
    print(f"  ✅ OPENAI_API_KEY: {key_preview}")
else:
    print(f"  ❌ OPENAI_API_KEY: Not set")
    print(f"     Set it in .env: OPENAI_API_KEY=sk-...")

print()

# Check optional dependencies
print("📦 Optional Dependencies:")
try:
    import psycopg2
    print("  ✅ psycopg2: Installed (SQL mode available)")
except ImportError:
    print("  ⚠️  psycopg2: Not installed (SQL mode unavailable, GraphQL only)")

try:
    import asyncpg
    print("  ✅ asyncpg: Installed (async SQL available)")
except ImportError:
    print("  ⚠️  asyncpg: Not installed (async SQL unavailable)")

print()

# Summary
print("=" * 60)
if settings.GRAPHQL_ENDPOINT and settings.OPENAI_API_KEY:
    print("✅ Setup looks good! You can start the service with:")
    print("   python3 main.py")
else:
    print("❌ Missing required configuration:")
    if not settings.GRAPHQL_ENDPOINT:
        print("   - GRAPHQL_ENDPOINT")
    if not settings.OPENAI_API_KEY:
        print("   - OPENAI_API_KEY")
    print()
    print("Update your .env file in the parent directory:")
    print("  GraphQL-MCP/.env")
print("=" * 60)


