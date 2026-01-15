#!/bin/bash

# =====================================================================
# Text-to-Cypher Endpoint Test Script
# =====================================================================
#
# This script tests the /graph/query endpoint which converts natural
# language queries to Cypher and executes them against KuzuDB.
#
# Prerequisites:
# 1. Backend server must be running: python api_server.py
# 2. DEBUG_MODE must be set to True in .env
# 3. KuzuDB must be initialized with data
#
# Usage:
#   bash test_text_to_cypher_endpoint.sh
#
# =====================================================================

# Configuration
BASE_URL="http://localhost:8000"
ENDPOINT="${BASE_URL}/graph/query"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "TEXT-TO-CYPHER ENDPOINT TESTS"
echo "======================================================================"
echo ""
echo "Testing endpoint: ${ENDPOINT}"
echo ""

# Test 1: Simple count query
echo -e "${BLUE}Test 1: How many projects are in the database?${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many projects are in the database?"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 2: List projects
echo -e "${BLUE}Test 2: List all projects${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List all projects with their names"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 3: Structural query
echo -e "${BLUE}Test 3: Count structural walls${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many structural walls are there?"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 4: Project-specific query
echo -e "${BLUE}Test 4: Query walls in a specific project${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all walls in project 25-01-161"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 5: Aggregation query
echo -e "${BLUE}Test 5: Count beams by level${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Count beams by level"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 6: Invalid query (should be rejected by verifier)
echo -e "${BLUE}Test 6: Invalid query - attempt to delete (should be rejected)${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Delete all projects"
  }' | jq '.'

echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 7: Neo4j-specific syntax (should be rejected by verifier)
echo -e "${BLUE}Test 7: Neo4j-specific syntax (should be rejected by KuzuDB compatibility check)${NC}"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the id of all projects"
  }' | jq '.'

echo ""
echo "======================================================================"
echo "TEST SUITE COMPLETE"
echo "======================================================================"
echo ""
echo -e "${YELLOW}Expected Results:${NC}"
echo "  Test 1-5: success=true, with cypher_query and results"
echo "  Test 6-7: success=false, verification_result.approved=false"
echo ""
echo -e "${GREEN}Check the DEBUG_MODE logs in the backend for detailed Cypher queries.${NC}"
