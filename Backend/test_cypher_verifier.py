"""
Test script for Cypher Verification Agent

Tests various scenarios to ensure the verifier correctly:
1. Approves safe, valid queries
2. Rejects write operations
3. Detects schema violations
4. Adds LIMIT clauses when missing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from nodes.DBRetrieval.KGdb.cypher_verifier import verify_cypher_query
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s'
)

def test_case(name: str, query: str, expected_approved: bool):
    """Run a single test case."""
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)
    print(f"Query: {query}")
    print("-" * 80)

    result = verify_cypher_query(query)

    print(f"Approved: {result['approved']}")
    print(f"Safety: {result['safety_passed']}")
    print(f"Schema: {result['schema_passed']}")
    print(f"Syntax: {result['syntax_passed']}")

    if result.get('issues'):
        print(f"Issues: {', '.join(result['issues'])}")

    if result.get('warnings'):
        print(f"Warnings: {', '.join(result['warnings'])}")

    if result.get('corrected_query'):
        print(f"Corrected Query: {result['corrected_query']}")

    print(f"Reasoning: {result.get('reasoning', 'N/A')}")

    # Verify expectation
    if result['approved'] == expected_approved:
        print("✅ TEST PASSED")
    else:
        print(f"❌ TEST FAILED - Expected approved={expected_approved}, got {result['approved']}")

    return result['approved'] == expected_approved


def run_all_tests():
    """Run all verification test cases."""
    print("\n" + "��️" * 40)
    print("CYPHER VERIFIER TEST SUITE")
    print("🛡️" * 40)

    results = []

    # Test 1: Simple safe query
    results.append(test_case(
        name="Test 1: Simple Project Count (SAFE)",
        query="MATCH (p:Project) RETURN count(p) AS project_count",
        expected_approved=True
    ))

    # Test 2: Write operation (should REJECT)
    results.append(test_case(
        name="Test 2: DELETE Operation (REJECT)",
        query="MATCH (p:Project) DELETE p",
        expected_approved=False
    ))

    # Test 3: Complex traversal with filter
    results.append(test_case(
        name="Test 3: Complex Traversal (SAFE)",
        query="""MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall)
WHERE p.name CONTAINS '2025' AND w.structural = true
RETURN p.name, count(w) AS wall_count
LIMIT 50""",
        expected_approved=True
    ))

    # Test 4: Query without LIMIT (should approve but suggest correction)
    results.append(test_case(
        name="Test 4: Query Without LIMIT (APPROVE with warning)",
        query="MATCH (p:Project) RETURN p.name, p.description",
        expected_approved=True
    ))

    # Test 5: CREATE operation (should REJECT)
    results.append(test_case(
        name="Test 5: CREATE Operation (REJECT)",
        query="CREATE (p:Project {name: 'Test'}) RETURN p",
        expected_approved=False
    ))

    # Test 6: MERGE operation (should REJECT)
    results.append(test_case(
        name="Test 6: MERGE Operation (REJECT)",
        query="MERGE (p:Project {name: 'Test'}) RETURN p",
        expected_approved=False
    ))

    # Test 7: Invalid node label (should REJECT if LLM catches it)
    results.append(test_case(
        name="Test 7: Invalid Node Label (SHOULD REJECT)",
        query="MATCH (x:InvalidNode) RETURN x LIMIT 10",
        expected_approved=False
    ))

    # Test 8: Query with Column (reserved keyword with backticks)
    results.append(test_case(
        name="Test 8: Column with Backticks (SAFE)",
        query="MATCH (c:`Column`) RETURN c.id, c.family LIMIT 20",
        expected_approved=True
    ))

    # Test 9: Aggregation query
    results.append(test_case(
        name="Test 9: Aggregation Query (SAFE)",
        query="""MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)
WITH p, v
OPTIONAL MATCH (v)-[:REFERENCES_WALL]->(w:Wall)
RETURN p.name AS ProjectName, COUNT(DISTINCT w) AS Walls
ORDER BY Walls DESC
LIMIT 15""",
        expected_approved=True
    ))

    # Test 10: SET operation (should REJECT)
    results.append(test_case(
        name="Test 10: SET Operation (REJECT)",
        query="MATCH (p:Project) SET p.updated = true RETURN p",
        expected_approved=False
    ))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
