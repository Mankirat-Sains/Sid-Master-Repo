#!/bin/bash
# Script to remove nested .git directories

cd "$(dirname "$0")"

echo "Removing nested .git directories..."

# Remove each nested .git directory
rm -rf ./localagent-JH/excelagent/speckleexcel/.git
rm -rf "./superceded_JH/JSON PIPELINE/.git"
rm -rf ./superceded_JH/Data-Processing-/.git
rm -rf ./sandbox-JH/GraphQL-MCP/.git
rm -rf ./sandbox-JH/IFC-MCP/ifcMCP/.git
rm -rf ./sandbox-JH/Specklepyquery/.git
rm -rf ./sandbox-JH/Specklepyquery/specklerepo/.git

echo "Done! Nested .git directories removed."
echo ""
echo "You can now run:"
echo "  git add -A"
echo "  git commit -m 'Remove nested git repositories'"
echo "  git push origin main"

