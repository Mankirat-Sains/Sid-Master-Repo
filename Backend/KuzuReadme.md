# Kuzu Graph Database Guide

**⚠️ IMPORTANT: DEBUG MODE REQUIRED**
To use the curl commands below, you must have `DEBUG_MODE=True` set in your `.env` file or environment variables. This enables the HTTP endpoints for the graph database.

**🤖 NOTE ON AI AGENT USAGE**
The AI agent does **NOT** use these `curl` commands or the HTTP API. It communicates directly with the database via the internal Python `KuzuManager` for maximum performance and security. The examples below are provided solely for developers to verify the database state and debug graph data manually.

## Overview

Kuzu is our embedded graph database running locally within the backend process. It models the relationships between Users, Projects, Models, Versions, and BIM Elements (Walls, Floors, etc.).

### Performance & Data Notice
- **Initial Load:** When loading the database for the first time (initialization), it may take **30-50 seconds** to process the schema and data insertions. After this initial setup, all Cypher queries are extremely fast, typically returning results in **less than a second**.
- **Project Data:** The database is currently pre-populated with **26 hardcoded projects**.
- **Future Roadmap:** Ideally, in the future, every new project that gets added to the system should be automatically synchronized and added to the user's Kuzu graph database for real-time relationship mapping.

## API Endpoints

There are **two ways** to query the Kuzu graph database via HTTP:

### 1. Natural Language Queries (Text-to-Cypher) - **RECOMMENDED**
**Endpoint:** `POST /graph/query`

This endpoint accepts natural language questions and automatically converts them to Cypher queries using AI. The system includes:
- **Automatic Cypher generation** from plain English
- **5-level verification** (safety, schema, syntax, KuzuDB compatibility, complexity)
- **Agent-based validation** to prevent dangerous operations
- **Detailed metadata** including confidence scores and reasoning

**Example:**
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "How many structural walls are in the Westlake project?"
     }'
```

**Response includes:**
- `success`: Whether the query succeeded
- `cypher_query`: The generated Cypher query (for transparency)
- `verification_result`: 5-level verification details
- `columns`: Column names from the result
- `rows`: Actual data returned
- `row_count`: Number of results
- `reasoning`: Why this Cypher was generated
- `confidence`: AI confidence score (0.0 to 1.0)
- `latency_ms`: Execution time

### 2. Direct Cypher Queries - **ADVANCED**
**Endpoint:** `POST /graph/cypher`

For developers who want full control, you can send raw Cypher queries directly. This endpoint **bypasses** the verification system and executes queries as-is.

**Example:**
```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "MATCH (p:Project) RETURN p.name LIMIT 10;"
     }'
```

**⚠️ Use with caution:** This endpoint does not validate queries for safety or compatibility.

---

## Natural Language Query Examples

Below are examples using the **Text-to-Cypher endpoint** (`/graph/query`) with natural language:

### Basic Counting
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "How many projects are in the database?"}'
```

### Filtering by Properties
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me all structural walls taller than 10 feet"}'
```

### Project-Specific Queries
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "List all walls in project 25-01-161"}'
```

### Aggregations
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Count beams by level"}'
```

### Relationship Traversals
```bash
curl -X POST "http://localhost:8000/graph/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Who owns the Westlake project?"}'
```

---

## Direct Cypher Query Examples

Below are examples using the **direct Cypher endpoint** (`/graph/cypher`) for advanced users:

**Note:** These examples use raw Cypher syntax. For most use cases, the natural language endpoint (`/graph/query`) is easier and safer.

### 1. Count All Nodes by Type
Get a summary count of all node types in the graph.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (n:User) RETURN 'Users' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Project) RETURN 'Projects' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Model) RETURN 'Models' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Version) RETURN 'Versions' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Wall) RETURN 'Walls' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Floor) RETURN 'Floors' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Roof) RETURN 'Roofs' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Beam) RETURN 'Beams' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:`Column`) RETURN 'Columns' AS NodeType, COUNT(n) AS Count UNION ALL MATCH (n:Ceiling) RETURN 'Ceilings' AS NodeType, COUNT(n) AS Count;"
}
EOF
```

### 2. List All Projects
Show all projects with their names and creation dates.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project) RETURN p.name AS ProjectName, p.description AS Description, p.createdAt AS CreatedDate ORDER BY p.createdAt DESC LIMIT 20;"
}
EOF
```

### 3. Find Projects with Most Models
Count how many models each project contains.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model) RETURN p.name AS ProjectName, COUNT(m) AS ModelCount ORDER BY ModelCount DESC LIMIT 10;"
}
EOF
```

### 4. Find All Walls in a Specific Project
List all walls in the "Westlake Linel Opening" project.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project {name: 'Westlake Linel Opening (25-01-161)'})-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall) RETURN w.id AS WallID, w.family AS Family, w.type AS Type, w.height AS Height, w.structural AS IsStructural LIMIT 20;"
}
EOF
```

### 5. Count Elements by Type in Each Project
For each project, count how many walls, floors, etc. it has.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version) OPTIONAL MATCH (v)-[:REFERENCES_WALL]->(w:Wall) OPTIONAL MATCH (v)-[:REFERENCES_FLOOR]->(f:Floor) OPTIONAL MATCH (v)-[:REFERENCES_ROOF]->(r:Roof) OPTIONAL MATCH (v)-[:REFERENCES_BEAM]->(b:Beam) OPTIONAL MATCH (v)-[:REFERENCES_COLUMN]->(c:`Column`) RETURN p.name AS ProjectName, COUNT(DISTINCT w) AS Walls, COUNT(DISTINCT f) AS Floors, COUNT(DISTINCT r) AS Roofs, COUNT(DISTINCT b) AS Beams, COUNT(DISTINCT c) AS Columns ORDER BY (COUNT(DISTINCT w) + COUNT(DISTINCT f) + COUNT(DISTINCT r) + COUNT(DISTINCT b) + COUNT(DISTINCT c)) DESC LIMIT 15;"
}
EOF
```

### 6. Find All Structural Walls
List all walls marked as structural.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.structural = true RETURN w.id AS WallID, w.family AS Family, w.type AS Type, w.height AS Height, w.level_name AS Level LIMIT 20;"
}
EOF
```

### 7. Find Tallest Walls
Find the walls with the greatest height.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.height IS NOT NULL RETURN w.id AS WallID, w.family AS Family, w.type AS Type, w.height AS Height, w.level_name AS Level ORDER BY w.height DESC LIMIT 10;"
}
EOF
```

### 8. Find Elements by Level
Find all walls on a specific level (e.g., "T/O FLOOR").

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.level_name = 'T/O FLOOR' RETURN w.id AS WallID, w.family AS Family, w.type AS Type, w.height AS Height LIMIT 20;"
}
EOF
```

### 9. Find All Unique Wall Types
List all unique wall type names and count how many of each.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.type IS NOT NULL RETURN w.type AS WallType, COUNT(w) AS Count ORDER BY Count DESC LIMIT 20;"
}
EOF
```

### 10. Find Projects with Beams
List only projects that contain beam elements.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)-[:REFERENCES_BEAM]->(b:Beam) RETURN DISTINCT p.name AS ProjectName, COUNT(b) AS BeamCount ORDER BY BeamCount DESC;"
}
EOF
```

### 11. Find the Largest Floors by Area
Identify floors with the largest surface area (assumes materialQuantities contains data).

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (f:Floor) WHERE f.materialQuantities IS NOT NULL RETURN f.id AS FloorID, f.type AS Type, f.level_name AS Level, f.materialQuantities AS Materials LIMIT 10;"
}
EOF
```

### 12. Full Path from User to Wall Element
Trace the complete hierarchy from user to a specific wall.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH path = (u:User)-[:OWNS]->(p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall) RETURN u.name AS UserName, p.name AS ProjectName, m.name AS ModelName, v.message AS VersionMessage, w.type AS WallType LIMIT 5;"
}
EOF
```

### 13. Find Elements Created in Specific Phase
Find all walls created in "New Construction" phase.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.phaseCreated = 'New Construction' RETURN w.id AS WallID, w.family AS Family, w.type AS Type, w.phaseCreated AS Phase LIMIT 20;"
}
EOF
```

### 14. Count Elements by Material Type
Find walls by their primary material (e.g., 'Concrete') using string matching.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.materialQuantities CONTAINS 'Concrete' RETURN w.id AS WallID, w.type AS Type, w.materialQuantities AS Materials LIMIT 15;"
}
EOF
```

### 15. Find All Versions and Their Creation Dates
List all versions with their messages and timestamps.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version) RETURN p.name AS ProjectName, m.name AS ModelName, v.id AS VersionID, v.message AS Message, v.sourceApplication AS Source, v.createdAt AS CreatedDate ORDER BY v.createdAt DESC LIMIT 20;"
}
EOF
```

### 16. Find Columns and Their Levels
List all columns with their level information.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (c:`Column`) RETURN c.id AS ColumnID, c.family AS Family, c.type AS Type, c.level_name AS Level, c.level_elevation AS Elevation ORDER BY c.level_elevation LIMIT 20;"
}
EOF
```

### 17. Find Elements with Baseline Geometry
Find walls that have baseline geometry (start/end points).

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (w:Wall) WHERE w.baseline_start_x IS NOT NULL RETURN w.id AS WallID, w.type AS Type, w.baseline_start_x AS StartX, w.baseline_start_y AS StartY, w.baseline_end_x AS EndX, w.baseline_end_y AS EndY, w.baseline_length AS Length LIMIT 15;"
}
EOF
```

### 18. Find Projects by Visibility
List projects and their visibility settings.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project) RETURN p.name AS ProjectName, p.visibility AS Visibility, p.role AS UserRole, p.createdAt AS CreatedDate ORDER BY p.visibility, p.createdAt DESC;"
}
EOF
```

### 19. Find Roofs and Their Associated Projects
List all roofs with their project context.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)-[:REFERENCES_ROOF]->(r:Roof) RETURN p.name AS ProjectName, r.id AS RoofID, r.type AS RoofType, r.level_name AS Level, r.slope AS Slope LIMIT 20;"
}
EOF
```

### 20. Complex Query - Find Project with Most Structural Elements
Calculate which project has the most structural walls and columns combined.

```bash
curl -X POST "http://localhost:8000/graph/cypher" \
     -H "Content-Type: application/json" \
     -d @- <<'EOF'
{
  "query": "MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version) OPTIONAL MATCH (v)-[:REFERENCES_WALL]->(w:Wall) WHERE w.structural = true OPTIONAL MATCH (v)-[:REFERENCES_COLUMN]->(c:`Column`) WITH p, COUNT(DISTINCT w) AS StructuralWalls, COUNT(DISTINCT c) AS Columns RETURN p.name AS ProjectName, StructuralWalls, Columns, (StructuralWalls + Columns) AS TotalStructuralElements ORDER BY TotalStructuralElements DESC LIMIT 10;"
}
EOF
```