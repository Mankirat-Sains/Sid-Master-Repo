# KuzuDB vs Neo4j Cypher Compatibility

## Overview

KuzuDB uses standard Cypher but has important differences from Neo4j. The Cypher verification agent now includes **KuzuDB compatibility checks** to reject Neo4j-specific syntax.

## Key Differences

### 1. Node/Relationship Introspection Functions

❌ **Neo4j (NOT SUPPORTED in KuzuDB):**
```cypher
MATCH (p:Project) RETURN id(p), labels(p)
MATCH (a)-[r]->(b) RETURN type(r)
MATCH (p:Project) RETURN properties(p)
```

✅ **KuzuDB (CORRECT):**
```cypher
MATCH (p:Project) RETURN p.id, p.name
// Labels are implicit - just use the node label in MATCH
// Properties must be accessed individually
```

### 2. Subquery Syntax

❌ **Neo4j (NOT SUPPORTED in KuzuDB):**
```cypher
MATCH (p:Project) WHERE EXISTS { MATCH (p)-[:OWNS]->(m) } RETURN p
MATCH (p:Project) CALL { MATCH (p)-[:OWNS]->(m) RETURN m } RETURN p, m
```

✅ **KuzuDB (CORRECT):**
```cypher
MATCH (p:Project)
OPTIONAL MATCH (p)-[:OWNS]->(m)
WHERE m IS NOT NULL
RETURN p
```

### 3. Variable-Length Relationships

❌ **Neo4j (NOT SUPPORTED in KuzuDB):**
```cypher
MATCH (a)-[*]->(b) RETURN a, b  // Unbounded - will fail in KuzuDB
```

✅ **KuzuDB (CORRECT):**
```cypher
MATCH (a)-[*1..5]->(b) RETURN a, b  // Must specify upper bound
```

## Common Neo4j → KuzuDB Conversions

| Neo4j Syntax | KuzuDB Equivalent | Reason |
|--------------|-------------------|--------|
| `id(node)` | `node.id` | Use property access |
| `labels(node)` | N/A (implicit) | Labels defined in MATCH |
| `type(rel)` | N/A (implicit) | Type defined in MATCH |
| `properties(node)` | `node.prop1, node.prop2` | Access individually |
| `EXISTS { pattern }` | `OPTIONAL MATCH pattern WHERE ... IS NOT NULL` | Subquery syntax |
| `CALL { subquery }` | Use `WITH` clauses | Subquery syntax |
| `-[*]->` | `-[*1..10]->` | Bounded paths required |

## Verification Agent

The Cypher verification agent (`cypher_verifier.py`) now performs **5 validation checks**:

1. **Safety Validation** - Reject write operations (CREATE, MERGE, SET, DELETE, DROP)
2. **Schema Validation** - Verify node labels and relationships exist in schema
3. **Syntax Validation** - Check for valid Cypher syntax (MATCH...RETURN structure)
4. **KuzuDB Compatibility** ⭐ NEW - Reject Neo4j-specific syntax
5. **Complexity Validation** - Recommend LIMIT clauses and bounded queries

## Testing

Run the compatibility test suite:

```bash
cd Backend
python3 test_kuzu_compatibility.py
```

Expected output: `11 passed, 0 failed`

## References

- Verification prompt: [prompts/cypher_verifier_prompts.py](prompts/cypher_verifier_prompts.py)
- Verification logic: [nodes/DBRetrieval/KGdb/cypher_verifier.py](nodes/DBRetrieval/KGdb/cypher_verifier.py)
- Test suite: [test_kuzu_compatibility.py](test_kuzu_compatibility.py)
