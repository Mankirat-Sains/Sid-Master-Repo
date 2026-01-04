#!/usr/bin/env python3
"""
Autodesk APS (Forge) Setup Script
Loads environment variables and prints CLI commands for APS operations.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')

# Verify environment variables
print("=" * 60)
print("APS Environment Configuration")
print("=" * 60)
print(f"Client ID: {client_id if client_id else 'NOT FOUND'}")
print(f"Client Secret: {'*' * 20 if client_secret else 'NOT FOUND'}")
print("=" * 60)
print()

if not client_id or not client_secret:
    print("⚠️  WARNING: Missing client_id or client_secret in .env file!")
    print()
else:
    print("✅ Environment variables loaded successfully!")
    print()

# Print CLI commands
print("=" * 60)
print("APS CLI Commands (Copy/Paste Ready)")
print("=" * 60)
print()

# 1. Authenticate
print("1. Authenticate with APS:")
print("-" * 60)
print(f"aps auth login --client-id {client_id} --client-secret {client_secret}")
print()

# 2. Upload AppBundle
print("2. Upload AppBundle:")
print("-" * 60)
print("cd forge-ifc-exporter/bundle")
print("aps appbundle create IFCExportAppBundle --engine Revit --description \"Revit to IFC Export\" --zip IFCExportAppBundle.zip")
print()

# 3. Create Activity
print("3. Create Activity:")
print("-" * 60)
print("aps activity create IFCExportActivity --engine Revit --appbundle IFCExportAppBundle --description \"Export Revit to IFC\"")
print()

# 4. Run WorkItem
print("4. Run WorkItem (after uploading RVT file):")
print("-" * 60)
print("# First, upload your RVT file to OSS bucket")
print("aps oss upload <bucket-key> <local-rvt-file>")
print()
print("# Then create and run workitem")
print("aps workitem create IFCExportActivity \\")
print("  --input-rvt <oss-object-name> \\")
print("  --output-ifc output.ifc")
print()

# 5. Check WorkItem Status
print("5. Check WorkItem Status:")
print("-" * 60)
print("aps workitem status <workitem-id>")
print()

# 6. Download Results
print("6. Download Results:")
print("-" * 60)
print("aps workitem output <workitem-id> --output-dir ./output")
print()

print("=" * 60)
print("Note: Replace placeholders (<bucket-key>, <local-rvt-file>, etc.) with actual values")
print("=" * 60)

