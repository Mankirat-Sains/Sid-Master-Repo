# How Speckle Objects Come Together to Build Models

## The Big Picture

Think of it like building with LEGO bricks:
- Each **object** is a single brick (or assembly of bricks)
- Objects **reference** other objects to build bigger structures
- A **commit** is like a snapshot that says "this is the finished model"
- The **viewer** assembles all the bricks into the final 3D visualization

## The Connection Chain

```
Commit → Root Object → __closure (dependency map) → Child Objects → Referenced Objects → Geometry
```

## 1. The Entry Point: Commits

A **commit** is your entry point to a complete model. It's stored in the `commits` table:

```sql
-- Commits table structure
commits:
  id: "abc123def4"          -- Short commit ID
  referencedObject: "01e9dbf7c47963158f7594d4fc8dbfcb"  -- Points to root object
  author: "user123"
  message: "Added new building floor"
  createdAt: "2025-01-15"
```

The `referencedObject` is the **root object ID** - the top-level object that represents your entire model.

## 2. The Root Object: Starting Point

The root object is just a regular object in the `objects` table, but it's special because:
- It's referenced by a commit
- It contains a `__closure` property that lists ALL child objects
- It's the entry point for loading the entire model

## 3. The Magic: `__closure` Property

This is the **dependency graph** stored directly in the object's JSONB data:

```json
{
  "id": "01e9dbf7c47963158f7594d4fc8dbfcb",
  "speckle_type": "Base",
  "name": "Building Model",
  "__closure": {
    "wall_obj_1_id": 1,      // Direct child, depth 1
    "wall_obj_2_id": 1,
    "floor_obj_id": 1,
    "door_obj_id": 2,        // Nested child, depth 2
    "handle_obj_id": 3       // Deeply nested, depth 3
  },
  "elements": [
    { "referencedId": "wall_obj_1_id" },
    { "referencedId": "floor_obj_id" }
  ]
}
```

The `__closure` object maps:
- **Key**: Child object ID
- **Value**: Minimum depth (1 = direct child, 2 = grandchild, etc.)

## 4. Object References: Building the Graph

Objects link to other objects in multiple ways:

### A. Via `__closure` (Hierarchical Structure)
```json
{
  "id": "building_root",
  "__closure": {
    "wall_id": 1,
    "floor_id": 1
  }
}
```

### B. Via `referencedId` (Direct References)
```json
{
  "id": "wall_01",
  "speckle_type": "Wall",
  "faces": [
    {
      "referencedId": "face_geometry_id"  // Reference to geometry object
    }
  ]
}
```

### C. Via Nested Objects (Embedded)
```json
{
  "id": "room_01",
  "elements": [
    { "referencedId": "door_01" },
    { "referencedId": "window_01" }
  ],
  "transform": {
    "referencedId": "matrix_01"  // Reference to transformation
  }
}
```

## 5. Real Example: A Building Component

Let's trace a concrete column:

```json
// Root Object (from commit)
{
  "id": "commit_root_abc123",
  "__closure": {
    "structural_column_id": 1,
    "geometry_vertices_id": 2,
    "material_concrete_id": 2
  }
}

// Structural Column Object
{
  "id": "structural_column_id",
  "speckle_type": "RevitInstance",
  "type": "Concrete-Rectangular-Column",
  "family": "Concrete-Rectangular-Column",
  "category": "Structural Columns",
  "units": "ft",
  "elementId": "502803",
  "transform": {
    "referencedId": "transform_matrix_id"
  },
  "geometry": {
    "referencedId": "column_geometry_id"
  }
}

// Geometry Object (referenced)
{
  "id": "column_geometry_id",
  "speckle_type": "Mesh",
  "vertices": {
    "referencedId": "vertices_chunk_id"  // Large data in chunks
  },
  "faces": {
    "referencedId": "faces_chunk_id"
  }
}
```

## 6. How the Viewer Loads Everything

### Step 1: Start with Commit
```typescript
commit.referencedObject → "commit_root_abc123"
```

### Step 2: Load Root Object
```sql
SELECT * FROM objects WHERE id = 'commit_root_abc123'
```

### Step 3: Read `__closure` to Get All Children
```typescript
rootObject.__closure = {
  "structural_column_id": 1,
  "geometry_vertices_id": 2,
  "material_concrete_id": 2
}
```

### Step 4: Traverse the Graph (ObjectLoader2)

The **Traverser** class recursively loads all objects:

```58:112:c:\Users\shine\speckle1\speckle-server\packages\objectloader2\src\core\traverser.ts
  async traverseBase(base: Base, onProgress?: OnProgress): Promise<Base> {
    for (const ignoredProp of this.#options.excludeProps || []) {
      delete (base as never)[ignoredProp]
    }
    if (base.__closure) {
      const ids = Object.keys(base.__closure)
      const promises: Promise<Base>[] = []
      for (const id of ids) {
        promises.push(
          this.traverseBase(await this.#loader.getObject({ id }), onProgress)
        )
      }
      await Promise.all(promises)
    }
    delete (base as never)['__closure']

    // De-chunk
    if (base.speckle_type?.includes('DataChunk')) {
      const chunk = base as DataChunk
      if (chunk.data) {
        await this.traverseArray(chunk.data, onProgress)
      }
    }

    //other props
    for (const prop in base) {
      if (prop === '__closure') continue
      if (prop === 'referenceId') continue
      if (prop === 'speckle_type') continue
      if (prop === 'data') continue
      const baseProp = (base as unknown as Record<string, unknown>)[prop]
      if (isScalar(baseProp)) continue
      if (isBase(baseProp)) {
        await this.traverseBase(baseProp, onProgress)
      } else if (isReference(baseProp)) {
        await this.traverseBase(
          await this.#loader.getObject({ id: baseProp.referencedId }),
          onProgress
        )
      } else if (Array.isArray(baseProp)) {
        await this.traverseArray(baseProp, onProgress)
      }
    }
    if (onProgress) {
      onProgress({
        stage: 'construction',
        current:
          ++this.#traversedReferencesCount > this.#totalChildrenCount
            ? this.#totalChildrenCount
            : this.#traversedReferencesCount,
        total: this.#totalChildrenCount
      })
    }
    return base
  }
```

**What it does:**
1. Loads all objects from `__closure`
2. Follows `referencedId` links
3. Resolves nested objects and arrays
4. Replaces references with actual objects
5. Reconstructs the complete object graph

### Step 5: Render in 3D

Once all objects are loaded:
- Geometry objects (meshes, breps, etc.) → Converted to 3D shapes
- Materials → Applied to surfaces
- Transforms → Position objects correctly
- Hierarchies → Build parent-child relationships

## 7. Database Optimization: Closure Table

The `object_children_closure` table pre-computes all parent-child relationships:

```sql
object_children_closure:
  parent: "commit_root_abc123"
  child: "wall_obj_1_id"
  minDepth: 1
  streamId: "project_123"
```

This allows fast queries like:
- "Get all children of this object"
- "Get all objects at depth 2"
- "Count total descendants"

## 8. Complete Flow Diagram

```
┌─────────────┐
│   Commit    │
│  (Entry)    │
└──────┬──────┘
       │ referencedObject
       ↓
┌──────────────────┐
│   Root Object    │
│  (Top Level)     │
│                  │
│  __closure: {    │
│    obj1: 1,      │
│    obj2: 1,      │
│    obj3: 2       │
│  }               │
└──────┬───────────┘
       │
       ├───→ Object 1 (Wall)
       │     ├───→ Geometry (faces, vertices)
       │     └───→ Material
       │
       ├───→ Object 2 (Floor)
       │     └───→ Geometry
       │
       └───→ Object 3 (Door - nested)
             ├───→ Geometry
             └───→ Handle (nested deeper)
                   └───→ Geometry

All objects loaded → Complete 3D Model
```

## 9. Key Insights

1. **Content-Addressed**: Object IDs are hashes of their content. Same content = same ID. This enables:
   - Deduplication (reuse same geometry across models)
   - Immutability (objects never change)
   - Caching (no need to reload unchanged objects)

2. **Lazy Loading**: Objects are loaded on-demand as references are resolved

3. **Chunking**: Large geometry data (vertices, faces) is split into chunks to:
   - Stay under size limits
   - Enable streaming
   - Allow partial loading

4. **Graph Structure**: It's a directed graph (DAG - Directed Acyclic Graph):
   - Objects can have multiple parents
   - Objects can reference the same geometry
   - No cycles (would break the system)

5. **Separation of Concerns**:
   - **Structure** (walls, floors) stored separately
   - **Geometry** (mesh data) stored separately  
   - **Materials** stored separately
   - **Transforms** stored separately
   - All linked by references

## 10. Example Query: Find All Objects in a Model

```sql
-- Get the commit's root object
SELECT "referencedObject" FROM commits WHERE id = 'abc123def4';

-- Get all child objects using closure
WITH RECURSIVE object_tree AS (
  -- Start with root object
  SELECT id, data->'__closure' as closure
  FROM objects 
  WHERE id = (SELECT "referencedObject" FROM commits WHERE id = 'abc123def4')
  
  UNION ALL
  
  -- Get all children
  SELECT o.id, o.data->'__closure' as closure
  FROM objects o
  JOIN object_tree ot ON o.id = ANY(SELECT jsonb_object_keys(ot.closure))
)
SELECT DISTINCT id FROM object_tree;
```

## Summary

**From Database to 3D Model:**
1. Commit points to root object
2. Root object's `__closure` lists all children
3. Traverser recursively loads all referenced objects
4. References are resolved (geometry, materials, transforms)
5. Complete object graph is assembled
6. Viewer renders the graph as a 3D model

The "shit ton of info" becomes a beautiful 3D model through this elegant graph traversal and reference resolution system!





