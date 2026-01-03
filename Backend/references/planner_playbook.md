# Engineering RAG Planner Playbook
 
## Core Engineering Knowledge
 
### Document Structure Understanding
- **Title Blocks**: Bottom-right corner, contains designer info, project number, date
- **General Notes**: Usually page 1, contains foundation requirements, general specs  
- **Foundation Notes**: Specific to foundation design, slab requirements
- **Structural Details**: Detail drawings showing construction methods
 
### Engineering Element Patterns
 
#### Floating Slabs
- **Keywords**: "floating slab"
- **Locations**: foundation notes, general notes, structural notes, foundation plan
- **Indicators**: slab thickness, reinforcement, vapor barrier, insulation
- **Strategy**: Look in foundation notes first, then general notes for slab specifications
 
#### Designer Identification  
- **Waddell Engineering Patterns**: "Waddell Engineering", "Waddell & Associates", "WE-", "W&E-"
- **Typical Locations**: title block, sheet title, drawing border, bottom-right corner
- **Strategy**: Check title blocks in bottom-right corner for firm name
 
#### Retaining Walls
- **Keywords**: "retaining wall", "R.W.", "R/W", "gravity wall", "cantilever wall"
- **Locations**: site plan, foundation plan, structural details, wall sections
- **Indicators**: wall height, reinforcement, drainage, backfill
- **Strategy**: Search site plans for wall locations, then structural details for specifications
 
#### Roof Trusses
- **Keywords**: "roof truss", "truss", "joist", "rafter", "beam", "framing"
- **Locations**: roof plan, structural plan, framing plan, roof framing
- **Indicators**: truss spacing, span, load, bracing, truss type
- **Strategy**: Check roof plans for truss layout, then structural details for specifications

#### Barndominium
- **Keywords**: "barndominium", "barn home", "shouse", "shop house", "metal building home", "pole barn home"
- **Locations**: floor plan, site plan, general notes, building type notes, title block
- **Indicators**: metal building frame, residential living space, shop/garage area, clear span, post frame construction
- **Common Features**: open floor plans, high ceilings, exposed beams, concrete slab foundation, metal siding/roofing
- **Strategy**: Look for combination residential/agricultural or residential/workshop spaces in floor plans, check general notes for "metal building" or "pre-engineered building" references, identify large clear-span areas typical of barn structures

 
## Query Strategy Examples
 
### Multi-Criteria Search
**Example**: "Find projects with floating slabs designed by Waddell Engineering"
**Strategy**:
1. Search foundation notes for 'floating slab', 'slab on grade' keywords
2. Search title blocks for 'Waddell Engineering', 'WE-' patterns
3. Cross-reference projects that appear in both searches
4. Verify designer info in title block bottom-right corner
 
### Specification Search
**Example**: "Find retaining walls over 8 feet high"
**Strategy**:
1. Search structural details for 'retaining wall', 'R.W.' keywords
2. Look for height dimensions in wall sections
3. Check site plans for wall elevations and locations
4. Filter for walls with height > 8'-0"
 
### Designer Verification
**Example**: "Find projects designed by Waddell Engineering"
**Strategy**:
1. Check title blocks on multiple sheets
2. Look for consistent designer patterns
3. Verify professional stamps and signatures
4. Cross-check with project metadata if available
 
## Planning Process
 
### Step 1: Analyze Query
- Identify engineering elements being asked about
- Determine if multiple criteria are involved
- Recognize if designer identification is needed
 
### Step 2: Determine Document Locations
- Map engineering elements to likely document locations
- Consider document structure and typical information placement
- Plan search sequence (most specific to most general)
 
### Step 3: Create Search Strategy
- Break complex queries into specific subqueries
- Plan cross-referencing for multi-criteria searches
- Include verification steps for designer identification
 
### Step 4: Generate Retrieval Steps
- Create specific search queries with engineering keywords
- Plan document location targeting
- Include validation and verification steps