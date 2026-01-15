// =====================================================================
// Sample Cypher Queries for Speckle BIM Knowledge Graph
// =====================================================================
//
// INSTRUCTIONS:
// - Copy and paste ONE query at a time into your KuzuDB CLI
// - Do NOT run multiple queries at once
// - Each query is independent and can be run in any order
// - Results will vary based on your actual data
//
// =====================================================================

// =====================================================================
// QUERY 1: Count All Nodes by Type
// =====================================================================
// Description: Get a summary count of all node types in the graph
// Use case: Understanding the overall composition of your knowledge graph

MATCH (n:User) RETURN 'Users' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Project) RETURN 'Projects' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Model) RETURN 'Models' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Version) RETURN 'Versions' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Wall) RETURN 'Walls' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Floor) RETURN 'Floors' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Roof) RETURN 'Roofs' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Beam) RETURN 'Beams' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:`Column`) RETURN 'Columns' AS NodeType, COUNT(n) AS Count
UNION ALL
MATCH (n:Ceiling) RETURN 'Ceilings' AS NodeType, COUNT(n) AS Count;


// =====================================================================
// QUERY 2: List All Projects
// =====================================================================
// Description: Show all projects with their names and creation dates
// Use case: Getting an overview of all projects in the system

MATCH (p:Project)
RETURN p.name AS ProjectName,
       p.description AS Description,
       p.createdAt AS CreatedDate
ORDER BY p.createdAt DESC
LIMIT 20;


// =====================================================================
// QUERY 3: Find Projects with Most Models
// =====================================================================
// Description: Count how many models each project contains
// Use case: Identifying which projects have the most BIM models

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)
RETURN p.name AS ProjectName,
       COUNT(m) AS ModelCount
ORDER BY ModelCount DESC
LIMIT 10;


// =====================================================================
// QUERY 4: Find All Walls in a Specific Project
// =====================================================================
// Description: List all walls in the "Westlake Linel Opening" project
// Use case: Exploring elements in a specific project
// Note: Replace project name with your actual project name

MATCH (p:Project {name: 'Westlake Linel Opening (25-01-161)'})-[:CONTAINS_MODEL]->(m:Model)
      -[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall)
RETURN w.id AS WallID,
       w.family AS Family,
       w.type AS Type,
       w.height AS Height,
       w.structural AS IsStructural
LIMIT 20;


// =====================================================================
// QUERY 5: Count Elements by Type in Each Project
// =====================================================================
// Description: For each project, count how many walls, floors, etc. it has
// Use case: Understanding the composition of different projects

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)
WITH p, v
OPTIONAL MATCH (v)-[:REFERENCES_WALL]->(w:Wall)
WITH p, v, COUNT(DISTINCT w) AS Walls
OPTIONAL MATCH (v)-[:REFERENCES_FLOOR]->(f:Floor)
WITH p, v, Walls, COUNT(DISTINCT f) AS Floors
OPTIONAL MATCH (v)-[:REFERENCES_ROOF]->(r:Roof)
WITH p, v, Walls, Floors, COUNT(DISTINCT r) AS Roofs
OPTIONAL MATCH (v)-[:REFERENCES_BEAM]->(b:Beam)
WITH p, v, Walls, Floors, Roofs, COUNT(DISTINCT b) AS Beams
OPTIONAL MATCH (v)-[:REFERENCES_COLUMN]->(c:`Column`)
WITH p, Walls, Floors, Roofs, Beams, COUNT(DISTINCT c) AS Columns
RETURN p.name AS ProjectName,
       Walls,
       Floors,
       Roofs,
       Beams,
       Columns
ORDER BY (Walls + Floors + Roofs + Beams + Columns) DESC
LIMIT 15;


// =====================================================================
// QUERY 6: Find All Structural Walls
// =====================================================================
// Description: List all walls marked as structural
// Use case: Identifying load-bearing walls across all projects

MATCH (w:Wall)
WHERE w.structural = true
RETURN w.id AS WallID,
       w.family AS Family,
       w.type AS Type,
       w.height AS Height,
       w.level_name AS Level
LIMIT 20;


// =====================================================================
// QUERY 7: Find Tallest Walls
// =====================================================================
// Description: Find the walls with the greatest height
// Use case: Identifying tallest structural elements

MATCH (w:Wall)
WHERE w.height IS NOT NULL
RETURN w.id AS WallID,
       w.family AS Family,
       w.type AS Type,
       w.height AS Height,
       w.level_name AS Level
ORDER BY w.height DESC
LIMIT 10;


// =====================================================================
// QUERY 8: Find Elements by Level
// =====================================================================
// Description: Find all walls on a specific level (e.g., "T/O FLOOR")
// Use case: Filtering elements by building level

MATCH (w:Wall)
WHERE w.level_name = 'T/O FLOOR'
RETURN w.id AS WallID,
       w.family AS Family,
       w.type AS Type,
       w.height AS Height
LIMIT 20;


// =====================================================================
// QUERY 9: Find All Unique Wall Types
// =====================================================================
// Description: List all unique wall type names and count how many of each
// Use case: Understanding wall type diversity across projects

MATCH (w:Wall)
WHERE w.type IS NOT NULL
RETURN w.type AS WallType,
       COUNT(w) AS Count
ORDER BY Count DESC
LIMIT 20;


// =====================================================================
// QUERY 10: Find Projects with Beams
// =====================================================================
// Description: List only projects that contain beam elements
// Use case: Finding structural projects

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)
      -[:HAS_VERSION]->(v:Version)-[:REFERENCES_BEAM]->(b:Beam)
RETURN DISTINCT p.name AS ProjectName,
       COUNT(b) AS BeamCount
ORDER BY BeamCount DESC;


// =====================================================================
// QUERY 11: Find the Largest Floors by Area
// =====================================================================
// Description: Identify floors with the largest surface area
// Use case: Finding major floor slabs in projects
// Note: This assumes floors have area information in materialQuantities

MATCH (f:Floor)
WHERE f.materialQuantities IS NOT NULL
RETURN f.id AS FloorID,
       f.type AS Type,
       f.level_name AS Level,
       f.materialQuantities AS Materials
LIMIT 10;


// =====================================================================
// QUERY 12: Full Path from User to Wall Element
// =====================================================================
// Description: Trace the complete hierarchy from user to a specific wall
// Use case: Understanding data lineage and relationships

MATCH path = (u:User)-[:OWNS]->(p:Project)-[:CONTAINS_MODEL]->(m:Model)
             -[:HAS_VERSION]->(v:Version)-[:REFERENCES_WALL]->(w:Wall)
RETURN u.name AS UserName,
       p.name AS ProjectName,
       m.name AS ModelName,
       v.message AS VersionMessage,
       w.type AS WallType
LIMIT 5;


// =====================================================================
// QUERY 13: Find Elements Created in Specific Phase
// =====================================================================
// Description: Find all walls created in "New Construction" phase
// Use case: Filtering by construction phase

MATCH (w:Wall)
WHERE w.phaseCreated = 'New Construction'
RETURN w.id AS WallID,
       w.family AS Family,
       w.type AS Type,
       w.phaseCreated AS Phase
LIMIT 20;


// =====================================================================
// QUERY 14: Count Elements by Material Type
// =====================================================================
// Description: Find walls by their primary material (from materialQuantities)
// Use case: Material inventory analysis
// Note: This searches within the materialQuantities JSON string

MATCH (w:Wall)
WHERE w.materialQuantities CONTAINS 'Concrete'
RETURN w.id AS WallID,
       w.type AS Type,
       w.materialQuantities AS Materials
LIMIT 15;


// =====================================================================
// QUERY 15: Find All Versions and Their Creation Dates
// =====================================================================
// Description: List all versions with their messages and timestamps
// Use case: Understanding version history across projects

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)
RETURN p.name AS ProjectName,
       m.name AS ModelName,
       v.id AS VersionID,
       v.message AS Message,
       v.sourceApplication AS Source,
       v.createdAt AS CreatedDate
ORDER BY v.createdAt DESC
LIMIT 20;


// =====================================================================
// QUERY 16: Find Columns and Their Levels
// =====================================================================
// Description: List all columns with their level information
// Use case: Understanding column distribution across building levels

MATCH (c:`Column`)
RETURN c.id AS ColumnID,
       c.family AS Family,
       c.type AS Type,
       c.level_name AS Level,
       c.level_elevation AS Elevation
ORDER BY c.level_elevation
LIMIT 20;


// =====================================================================
// QUERY 17: Find Elements with Baseline Geometry
// =====================================================================
// Description: Find walls that have baseline geometry (start/end points)
// Use case: Analyzing geometric properties of linear elements

MATCH (w:Wall)
WHERE w.baseline_start_x IS NOT NULL
RETURN w.id AS WallID,
       w.type AS Type,
       w.baseline_start_x AS StartX,
       w.baseline_start_y AS StartY,
       w.baseline_end_x AS EndX,
       w.baseline_end_y AS EndY,
       w.baseline_length AS Length
LIMIT 15;


// =====================================================================
// QUERY 18: Find Projects by Visibility
// =====================================================================
// Description: List projects and their visibility settings (PUBLIC/PRIVATE)
// Use case: Understanding project access controls

MATCH (p:Project)
RETURN p.name AS ProjectName,
       p.visibility AS Visibility,
       p.role AS UserRole,
       p.createdAt AS CreatedDate
ORDER BY p.visibility, p.createdAt DESC;


// =====================================================================
// QUERY 19: Find Roofs and Their Associated Projects
// =====================================================================
// Description: List all roofs with their project context
// Use case: Roof inventory across all projects

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)
      -[:HAS_VERSION]->(v:Version)-[:REFERENCES_ROOF]->(r:Roof)
RETURN p.name AS ProjectName,
       r.id AS RoofID,
       r.type AS RoofType,
       r.level_name AS Level,
       r.slope AS Slope
LIMIT 20;


// =====================================================================
// QUERY 20: Complex Query - Find Project with Most Structural Elements
// =====================================================================
// Description: Calculate which project has the most structural walls and columns combined
// Use case: Identifying the most structurally complex project

MATCH (p:Project)-[:CONTAINS_MODEL]->(m:Model)-[:HAS_VERSION]->(v:Version)
OPTIONAL MATCH (v)-[:REFERENCES_WALL]->(w:Wall)
WHERE w.structural = true
OPTIONAL MATCH (v)-[:REFERENCES_COLUMN]->(c:`Column`)
WITH p, COUNT(DISTINCT w) AS StructuralWalls, COUNT(DISTINCT c) AS Columns
RETURN p.name AS ProjectName,
       StructuralWalls,
       Columns,
       (StructuralWalls + Columns) AS TotalStructuralElements
ORDER BY TotalStructuralElements DESC
LIMIT 10;


// =====================================================================
// END OF SAMPLE QUERIES
// =====================================================================
//
// TIPS FOR EXPLORATION:
// 1. Modify the LIMIT values to see more or fewer results
// 2. Change project names in WHERE clauses to explore different projects
// 3. Combine conditions using AND/OR in WHERE clauses
// 4. Use RETURN * to see all properties of nodes
// 5. Check your actual data first (Query 1 & 2) before running complex queries
//
// =====================================================================
