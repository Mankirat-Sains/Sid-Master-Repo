// =====================================================================
// BimDB - KuzuDB Schema for Speckle BIM Models
// =====================================================================
// Created: 2026-01-06
// Purpose: Graph database schema for storing Speckle BIM data
// Hierarchy: User → Project → Model → Version → BIM Objects
// =====================================================================

// =====================================================================
// ORGANIZATIONAL NODE TABLES
// =====================================================================

// User node table
CREATE NODE TABLE User (
    id STRING,
    name STRING,
    email STRING,
    avatar STRING,
    bio STRING,
    company STRING,
    role STRING,
    verified BOOLEAN,
    createdAt TIMESTAMP,
    PRIMARY KEY (id)
);

// Project node table
CREATE NODE TABLE Project (
    id STRING,
    name STRING,
    description STRING,
    workspaceId STRING,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    role STRING,
    visibility STRING,
    allowPublicComments BOOLEAN,
    PRIMARY KEY (id)
);

// Model node table
CREATE NODE TABLE Model (
    id STRING,
    name STRING,
    displayName STRING,
    description STRING,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    previewUrl STRING,
    PRIMARY KEY (id)
);

// Version node table (immutable snapshots)
CREATE NODE TABLE Version (
    id STRING,
    referencedObject STRING,
    message STRING,
    sourceApplication STRING,
    createdAt TIMESTAMP,
    previewUrl STRING,
    PRIMARY KEY (id)
);

// =====================================================================
// BIM ELEMENT NODE TABLES
// =====================================================================

// Wall node table
CREATE NODE TABLE Wall (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    height DOUBLE,
    baseOffset DOUBLE,
    topOffset DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    topLevel_name STRING,
    topLevel_elevation DOUBLE,
    topLevel_id STRING,
    // Revit-specific
    structural BOOLEAN,
    flipped BOOLEAN,
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Baseline geometry (embedded)
    baseline_type STRING,
    baseline_start_x DOUBLE,
    baseline_start_y DOUBLE,
    baseline_start_z DOUBLE,
    baseline_end_x DOUBLE,
    baseline_end_y DOUBLE,
    baseline_end_z DOUBLE,
    baseline_length DOUBLE,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Floor node table
CREATE NODE TABLE Floor (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    slope DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    structural BOOLEAN,
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Outline geometry (embedded as JSON)
    outline_type STRING,
    outline_points STRING,
    outline_closed BOOLEAN,
    voids STRING,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Roof node table
CREATE NODE TABLE Roof (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    slope DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Outline geometry (embedded as JSON)
    outline_type STRING,
    outline_points STRING,
    outline_closed BOOLEAN,
    voids STRING,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Beam node table
CREATE NODE TABLE Beam (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    structural BOOLEAN,
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Baseline geometry (embedded)
    baseline_type STRING,
    baseline_start_x DOUBLE,
    baseline_start_y DOUBLE,
    baseline_start_z DOUBLE,
    baseline_end_x DOUBLE,
    baseline_end_y DOUBLE,
    baseline_end_z DOUBLE,
    baseline_length DOUBLE,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Column node table (Column is a reserved keyword, use backticks)
CREATE NODE TABLE `Column` (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    height DOUBLE,
    baseOffset DOUBLE,
    topOffset DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    topLevel_name STRING,
    topLevel_elevation DOUBLE,
    topLevel_id STRING,
    // Revit-specific
    structural BOOLEAN,
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Baseline geometry (embedded)
    baseline_type STRING,
    baseline_start_x DOUBLE,
    baseline_start_y DOUBLE,
    baseline_start_z DOUBLE,
    baseline_end_x DOUBLE,
    baseline_end_y DOUBLE,
    baseline_end_z DOUBLE,
    baseline_length DOUBLE,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Ceiling node table
CREATE NODE TABLE Ceiling (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    slope DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Outline geometry (embedded as JSON)
    outline_type STRING,
    outline_points STRING,
    outline_closed BOOLEAN,
    voids STRING,
    // Material quantities (as JSON string)
    materialQuantities STRING,
    PRIMARY KEY (id)
);

// Door node table
CREATE NODE TABLE Door (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    PRIMARY KEY (id)
);

// Window node table
CREATE NODE TABLE Window (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    PRIMARY KEY (id)
);

// Pipe node table (MEP)
CREATE NODE TABLE Pipe (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    diameter DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Baseline geometry (embedded)
    baseline_type STRING,
    baseline_start_x DOUBLE,
    baseline_start_y DOUBLE,
    baseline_start_z DOUBLE,
    baseline_end_x DOUBLE,
    baseline_end_y DOUBLE,
    baseline_end_z DOUBLE,
    baseline_length DOUBLE,
    PRIMARY KEY (id)
);

// Duct node table (MEP)
CREATE NODE TABLE Duct (
    id STRING,
    speckle_type STRING,
    applicationId STRING,
    elementId STRING,
    units STRING,
    // Metadata
    family STRING,
    type STRING,
    category STRING,
    // Geometric properties
    width DOUBLE,
    height DOUBLE,
    // Level information (embedded)
    level_name STRING,
    level_elevation DOUBLE,
    level_id STRING,
    // Revit-specific
    builtInCategory STRING,
    phaseCreated STRING,
    worksetId INT64,
    isRevitLinkedModel BOOLEAN,
    revitLinkedModelPath STRING,
    // Baseline geometry (embedded)
    baseline_type STRING,
    baseline_start_x DOUBLE,
    baseline_start_y DOUBLE,
    baseline_start_z DOUBLE,
    baseline_end_x DOUBLE,
    baseline_end_y DOUBLE,
    baseline_end_z DOUBLE,
    baseline_length DOUBLE,
    PRIMARY KEY (id)
);

// =====================================================================
// RELATIONSHIP TABLES
// =====================================================================

// User owns Projects
CREATE REL TABLE OWNS (
    FROM User TO Project
);

// Project contains Models
CREATE REL TABLE CONTAINS_MODEL (
    FROM Project TO Model
);

// Model has Versions
CREATE REL TABLE HAS_VERSION (
    FROM Model TO Version
);

// Version references BIM elements
CREATE REL TABLE REFERENCES_WALL (
    FROM Version TO Wall
);

CREATE REL TABLE REFERENCES_FLOOR (
    FROM Version TO Floor
);

CREATE REL TABLE REFERENCES_ROOF (
    FROM Version TO Roof
);

CREATE REL TABLE REFERENCES_BEAM (
    FROM Version TO Beam
);

CREATE REL TABLE REFERENCES_COLUMN (
    FROM Version TO `Column`
);

CREATE REL TABLE REFERENCES_CEILING (
    FROM Version TO Ceiling
);

CREATE REL TABLE REFERENCES_DOOR (
    FROM Version TO Door
);

CREATE REL TABLE REFERENCES_WINDOW (
    FROM Version TO Window
);

CREATE REL TABLE REFERENCES_PIPE (
    FROM Version TO Pipe
);

CREATE REL TABLE REFERENCES_DUCT (
    FROM Version TO Duct
);

// Model created by User
CREATE REL TABLE CREATED_MODEL (
    FROM User TO Model
);

// Version created by User
CREATE REL TABLE CREATED_VERSION (
    FROM User TO Version
);

// =====================================================================
// SCHEMA NOTES
// =====================================================================
// 1. All IDs are Speckle content-addressable hashes (SHA256)
// 2. Level information is embedded directly into element nodes
// 3. Material quantities stored as JSON strings for flexibility
// 4. Geometric data embedded in element nodes (not separate nodes)
// 5. Timestamps use TIMESTAMP type for proper temporal queries
// 6. Boolean fields for flags (structural, flipped, closed, etc.)
// 7. speckle_type preserves full inheritance chain from Speckle
// 8. Units stored as strings (ft, m, mm, etc.)
// 9. Column is a reserved keyword, wrapped in backticks
// =====================================================================
