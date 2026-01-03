# Canonical Query Pattern Implementation

This service follows the canonical Speckle query pattern for efficient fact extraction.

## The Pattern

### Step A — Identify Model Scope (commit → root)

```sql
SELECT
  c.id AS commit_id,
  o.id AS root_object_id,
  o.data->'__closure' AS closure
FROM commits c
JOIN objects o ON o.id = c."referencedObject"
WHERE c.id = :commit_id;
```

**Purpose**: Get the model root and closure map to define the search boundary.

### Step B — Query Elements Within Scope

```sql
SELECT
  obj.id,
  obj.speckleType,
  obj.data
FROM objects obj
WHERE obj.id IN (
  SELECT key
  FROM jsonb_each_text(:closure)
)
AND obj.speckleType LIKE 'Objects.BuiltElements.%';
```

**Purpose**: Use closure to scope the query - only elements within the model.

### Step C — Filter for Engineering Meaning

```sql
-- Example: columns
AND obj.speckleType ILIKE '%Column%';

-- Example: material-based filtering
AND obj.data->'parameters'->'STRUCTURAL_MATERIAL_PARAM' IS NOT NULL;
```

**Purpose**: Apply coarse filters based on engineering intent.

### Step D — Extract Facts from JSONB

```python
# This happens in Phase 2 (Python extractors)
obj.data->'parameters'->'STRUCTURAL_MATERIAL_PARAM'->>'value'
```

**Purpose**: Precise fact extraction happens in Python, not SQL.

## GraphQL Implementation

For GraphQL queries, the pattern translates to:

1. **Get Project → Models → Versions → Commits**
2. **Get Commit → Referenced Object (root)**
3. **Extract Closure from Root Object**
4. **Query Objects in Closure**
5. **Filter by SpeckleType**

## Why This Works

✅ **Uses existing schema only** - No schema changes needed  
✅ **Uses Postgres indexes efficiently** - Closure-based queries are fast  
✅ **JSONB extraction only after scoping** - Never scans full database  
✅ **Works across disciplines + connectors** - Schema-agnostic  
✅ **Scales to millions of elements** - Closure limits search space  

## Key Principle

> Roots define the project boundary.  
> Objects define engineering reality.  
> Intelligence emerges from aggregation, not schema.


