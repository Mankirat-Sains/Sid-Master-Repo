# Project Categorization Rules

## Category Definitions

### Residential / House
- **Primary Keywords**: "house", "residence", "home", "gazebo", "pavilion", "deck", "accessory"
- **Indicators**: 
  - Single-family dwellings, residential structures
  - Accessory structures (gazebos, pavilions, decks) attached to or associated with residential properties
  - Living spaces, bedrooms, bathrooms, kitchen, residential occupancy
  - R-occupancy classification
- **Context Clues**: 
  - Project names containing "Residence", "Home", "House"
  - Addresses in residential neighborhoods
  - Accessory structures clearly associated with residential properties
- **Examples**: "Smith Residence", "123 Main St House", "Backyard Gazebo", "Deck Addition"

### Commercial
- **Primary Keywords**: 
  - "brewery", "winery", "distillery", "alcohol", "beer", "wine", "spirits"
  - "mechanic", "auto repair", "automotive", "car repair", "vehicle service"
  - "riding arena", "equestrian arena", "horse arena"
  - "TI", "tenant improvement", "tenant fit-out"
  - "medical", "dental", "pilates", "office", "clinic"
  - Projects associated with Mark Heimpel (commercial work indicator)
- **Indicators**: 
  - Business operations, commercial occupancy
  - Retail spaces, offices, professional services
  - Tenant improvements, commercial fit-outs
  - M-occupancy classification
- **Context Clues**: 
  - Project names indicating business types (e.g., "Main Street Brewery", "Auto Repair Shop")
  - Commercial addresses, business districts
  - Tenant improvement references
- **Special Notes**: 
  - Riding arenas are commercial (not agricultural) unless clearly part of a farm operation
  - Mark Heimpel projects are typically commercial
- **Examples**: "Downtown Office Building", "Brewery Facility", "Medical Clinic", "TI for Retail Space"

### Farm / Agricultural
- **Primary Keywords**: 
  - "barn", "shed", "shop" (when in agricultural context)
  - Farm animals: "sheep", "dairy", "cow", "cattle", "goat", "pig", "hog", "chicken", "poultry"
  - "farm", "agricultural", "livestock", "grain", "silo"
- **Indicators**: 
  - Animal housing structures
  - Agricultural equipment storage
  - Livestock facilities
  - Crop storage buildings
  - Farm operations
- **Context Clues**: 
  - Project names with farm/agricultural terms
  - Rural addresses, farm locations
  - References to livestock, crops, agricultural operations
- **Exclusions**: 
  - "Horse" alone is NOT a farm indicator (horses can be for riding arenas - commercial)
  - "Shop" in commercial/industrial context (not agricultural)
- **Examples**: "Dairy Barn", "Grain Storage Shed", "Livestock Barn", "Chicken Coop"

### Mixed-Use
- **Keywords**: "mixed use", "combination", "residential and commercial", "live-work", "barndominium"
- **Indicators**: Multiple distinct uses in one building
- **Examples**: "Barndominium" (residential + agricultural), "Live-Work Building"

### Industrial
- **Keywords**: "industrial", "warehouse", "factory", "manufacturing", "distribution", "I-occupancy", "storage"
- **Indicators**: Manufacturing facilities, warehouses, loading docks, industrial equipment
- **Note**: "Shop" can be industrial if context indicates manufacturing/industrial use

## Categorization Rules

1. **Primary Category**: Assign ONE primary category based on the dominant use/occupancy
2. **Keyword Matching**: 
   - Check project name, address, and drawing content for category keywords
   - Multiple keywords from same category = stronger match
   - Conflicting keywords = use context to determine primary use
3. **Context Priority**: 
   - Project name is strongest indicator
   - Drawing notes and specifications provide confirmation
   - Address context (residential vs commercial area) is supporting evidence
4. **Special Cases**:
   - **Riding Arena**: Commercial (unless clearly part of farm operation)
   - **Horse-related**: Only farm if explicitly agricultural context (livestock, breeding). Riding = commercial
   - **Shop**: Farm if agricultural context (farm shop, equipment storage). Commercial/Industrial if business/manufacturing context
   - **Accessory Structures**: Residential if associated with house/residence. Commercial if associated with commercial building
   - **Mark Heimpel Projects**: Typically commercial - use as strong indicator
5. **Default**: If unclear, use the most specific category that applies based on strongest keyword match

## Filtering Rules

- **"residential projects" / "houses" / "homes"**: ONLY include Residential/House category
- **"commercial projects" / "commercial buildings"**: ONLY include Commercial category
- **"farm projects" / "agricultural" / "barn"**: ONLY include Farm/Agricultural category
- **"breweries" / "wineries"**: ONLY include Commercial projects with brewery/winery keywords
- **"medical" / "dental" / "office"**: ONLY include Commercial projects with those specific keywords
- **"riding arena"**: ONLY include Commercial (not farm)
- **"Mark Heimpel projects"**: ONLY include Commercial projects

## Answer Organization

When listing multiple projects:
1. **Group by category** (Residential, Commercial, Farm, etc.)
2. **Within each category**, sort by date (newest first by project number)
3. **Use clear section headers**: 
   - "## Residential Projects"
   - "## Commercial Projects" 
   - "## Farm / Agricultural Projects"
4. **If all projects are same category**: You can omit category headers but mention the category in your introduction
5. **Mixed categories**: Always organize by category first, then by date within category

## Examples

**Query: "Find all residential projects"**
- Include: Houses, Residences, Homes, Gazebos (if residential), Pavilions (if residential), Decks (if residential)
- Exclude: Commercial, Farm, Industrial

**Query: "Show me brewery projects"**
- Include: Only projects with brewery/winery/distillery keywords
- Exclude: All other commercial, residential, farm projects

**Query: "Find barn projects"**
- Include: Farm barns, agricultural barns
- Exclude: Commercial structures, residential (unless barndominium)

**Query: "Show me Mark Heimpel projects"**
- Include: Commercial projects associated with Mark Heimpel
- Exclude: All other projects

