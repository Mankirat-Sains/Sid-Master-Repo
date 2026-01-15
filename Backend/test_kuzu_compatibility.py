"""
Test KuzuDB Compatibility Check

Tests the new Neo4j vs KuzuDB compatibility validation.
"""

import re

# Import the compatibility patterns
KUZU_INCOMPATIBLE_PATTERNS = {
    "id(": "Neo4j-specific function - use node.id property instead",
    "labels(": "Neo4j-specific function - labels are implicit in KuzuDB",
    "type(": "Neo4j-specific function - relationship types are implicit in KuzuDB",
    "properties(": "Neo4j-specific function - access properties individually",
    "EXISTS {": "Neo4j subquery syntax - use OPTIONAL MATCH with IS NOT NULL",
    "CALL {": "Neo4j subquery syntax - use WITH clauses instead",
}


def kuzu_compatibility_check(cypher_query: str) -> dict:
    """Check for Neo4j-specific syntax that's incompatible with KuzuDB."""
    # Check for Neo4j-specific patterns
    for pattern, description in KUZU_INCOMPATIBLE_PATTERNS.items():
        if pattern in cypher_query:
            return {
                "passed": False,
                "reason": f"Neo4j-specific syntax '{pattern}' detected - {description}"
            }

    # Check for unbounded variable-length relationships: -[*]-> or -[*]-
    unbounded_pattern = re.search(r'-\[\*\](-|>)', cypher_query)
    if unbounded_pattern:
        return {
            "passed": False,
            "reason": "Variable-length relationship '-[*]-' must have upper bound in KuzuDB (e.g., '-[*1..5]->')"
        }

    return {"passed": True, "reason": "No KuzuDB compatibility issues detected"}


def run_tests():
    """Run KuzuDB compatibility tests."""
    print("=" * 80)
    print("KUZU COMPATIBILITY CHECK TESTS")
    print("=" * 80)

    test_cases = [
        # Compatible queries (should PASS)
        ("Safe: Property access", "MATCH (p:Project) RETURN p.id, p.name LIMIT 10", True),
        ("Safe: Bounded path", "MATCH (a)-[*1..5]->(b) RETURN a, b LIMIT 10", True),
        ("Safe: OPTIONAL MATCH", "MATCH (p:Project) OPTIONAL MATCH (p)-[:OWNS]->(m) WHERE m IS NOT NULL RETURN p, m LIMIT 10", True),

        # Neo4j-specific (should FAIL)
        ("Neo4j: id() function", "MATCH (p:Project) RETURN id(p) LIMIT 10", False),
        ("Neo4j: labels() function", "MATCH (n) RETURN labels(n) LIMIT 10", False),
        ("Neo4j: type() function", "MATCH (a)-[r]->(b) RETURN type(r) LIMIT 10", False),
        ("Neo4j: properties() function", "MATCH (p:Project) RETURN properties(p) LIMIT 10", False),
        ("Neo4j: EXISTS subquery", "MATCH (p:Project) WHERE EXISTS { MATCH (p)-[:OWNS]->(m) } RETURN p LIMIT 10", False),
        ("Neo4j: CALL subquery", "MATCH (p:Project) CALL { MATCH (p)-[:OWNS]->(m) RETURN m } RETURN p, m LIMIT 10", False),
        ("Neo4j: Unbounded path", "MATCH (a)-[*]->(b) RETURN a, b LIMIT 10", False),
        ("Neo4j: Unbounded bidirectional", "MATCH (a)-[*]-(b) RETURN a, b LIMIT 10", False),
    ]

    passed = 0
    failed = 0

    for name, query, expected_compatible in test_cases:
        result = kuzu_compatibility_check(query)
        is_compatible = result["passed"]

        status = "✅ PASS" if is_compatible == expected_compatible else "❌ FAIL"
        print(f"\n{status} - {name}")
        print(f"  Query: {query[:70]}{'...' if len(query) > 70 else ''}")
        print(f"  Expected: {'COMPATIBLE' if expected_compatible else 'INCOMPATIBLE'}")
        print(f"  Got: {'COMPATIBLE' if is_compatible else 'INCOMPATIBLE'}")

        if not is_compatible:
            print(f"  Reason: {result['reason']}")

        if is_compatible == expected_compatible:
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
