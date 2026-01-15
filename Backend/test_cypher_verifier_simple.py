"""
Simple test for Cypher Verifier logic (without full environment)

Tests the rule-based safety checks and validation logic.
"""

import re

def rule_based_safety_check(cypher_query: str) -> dict:
    """Quick rule-based safety check for write operations."""
    query_upper = cypher_query.upper()
    write_operations = ["CREATE", "MERGE", "SET", "DELETE", "DROP", "DETACH", "REMOVE"]

    for operation in write_operations:
        if re.search(r'\b' + operation + r'\b', query_upper):
            return {
                "passed": False,
                "reason": f"{operation} operation detected - write operations are forbidden"
            }

    return {"passed": True, "reason": "No write operations detected"}


def run_tests():
    """Run basic safety check tests."""
    print("=" * 80)
    print("CYPHER VERIFIER - SAFETY CHECK TESTS")
    print("=" * 80)

    test_cases = [
        ("Safe: Simple SELECT", "MATCH (p:Project) RETURN p.name LIMIT 10", True),
        ("Safe: Aggregation", "MATCH (p:Project) RETURN count(p)", True),
        ("Unsafe: DELETE", "MATCH (p:Project) DELETE p", False),
        ("Unsafe: CREATE", "CREATE (p:Project {name: 'Test'})", False),
        ("Unsafe: MERGE", "MERGE (p:Project {name: 'Test'})", False),
        ("Unsafe: SET", "MATCH (p:Project) SET p.updated = true", False),
        ("Unsafe: DROP", "DROP TABLE Project", False),
        ("Safe: createdAt property", "MATCH (p:Project) RETURN p.createdAt", True),
        ("Safe: Complex query", "MATCH (p:Project)-[:CONTAINS_MODEL]->(m) RETURN p, m LIMIT 50", True),
    ]

    passed = 0
    failed = 0

    for name, query, expected_safe in test_cases:
        result = rule_based_safety_check(query)
        is_safe = result["passed"]

        status = "✅ PASS" if is_safe == expected_safe else "❌ FAIL"
        print(f"\n{status} - {name}")
        print(f"  Query: {query[:60]}{'...' if len(query) > 60 else ''}")
        print(f"  Expected: {'SAFE' if expected_safe else 'UNSAFE'}")
        print(f"  Got: {'SAFE' if is_safe else 'UNSAFE'}")

        if not is_safe:
            print(f"  Reason: {result['reason']}")

        if is_safe == expected_safe:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
