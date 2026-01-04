# Implementation Notes

## GraphQL Connection

The service now properly implements the canonical Speckle query pattern for GraphQL:

1. **Project → Models → Versions → Commits**: Traverses the project hierarchy
2. **Commit → Root Object**: Gets the referenced object (model root)
3. **Root → Closure**: Extracts the `__closure` map from root object data
4. **Closure → Elements**: Queries objects within the closure scope
5. **Filter by SpeckleType**: Applies coarse filters for engineering meaning

## Key Implementation Details

### GraphQL Client (`db/graphql_client.py`)

- `get_commit_root_and_closure()`: Step A - Gets root and closure
- `get_objects_in_closure()`: Step B - Queries elements within closure
- `discover_candidates_canonical()`: Orchestrates the full pattern

### SQL Queries (`db/queries.py`)

- `build_candidate_discovery_query()`: Builds SQL following the canonical pattern
- Uses CTE (Common Table Expression) for commit → root → closure
- Properly scopes queries using closure membership

### Executor (`executor/executor.py`)

- `_discover_candidates_graphql()`: Uses canonical GraphQL pattern
- `_discover_candidates_sql()`: Uses canonical SQL pattern
- Both follow the same logical flow: scope → filter → extract

## Data Structure

The service expects Speckle objects with this structure:

```json
{
  "id": "object_id",
  "speckleType": "Objects.BuiltElements.Column",
  "data": {
    "__closure": {
      "child_id_1": {},
      "child_id_2": {}
    },
    "parameters": {
      "STRUCTURAL_MATERIAL_PARAM": {
        "value": "timber"
      }
    },
    "properties": {
      "Quantities": {...}
    }
  }
}
```

## Fact Extraction

Extractors operate on the `data` JSONB field:

- **Material**: `data.parameters.STRUCTURAL_MATERIAL_PARAM.value`
- **Section**: `data.sectionName` or `data.properties.shape`
- **Level**: `data.level` or `data.levelRef.name`
- **Element Type**: Inferred from `speckleType`

## Testing

To test the GraphQL connection:

1. Set `GRAPHQL_ENDPOINT` in `.env`
2. Set `GRAPHQL_AUTH_TOKEN` if required
3. Run: `python main.py`
4. Query: `POST /query` with `{"question": "Do we have any timber columns?"}`

The service will:
1. Get projects via GraphQL
2. For each project, get latest version/commit
3. Extract root object and closure
4. Query objects in closure matching filters
5. Extract facts from JSONB data
6. Compose answer


