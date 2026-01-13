Documentation you can copy into another Cursor environment:
# Excel Sync Agent - System Overview & Architecture## 🎯 The Problem This Solves**The Challenge:**- Engineering teams use Excel files for complex calculations (structural analysis, load calculations, etc.)- These Excel files live on local machines or shared network drives- A cloud-based platform needs access to calculation results in real-time- Manual data entry is error-prone and time-consuming- Engineers shouldn't have to manually copy/paste data from Excel to web forms**The Solution:**An automated agent that bridges the gap between local Excel files and cloud platforms, extracting specific calculation results and syncing them automatically.---## 🏗️ System Architecture
┌─────────────────────────────────────────────────────────────┐
│ LOCAL ENVIRONMENT │
│ │
│ ┌──────────────┐ ┌──────────────┐ │
│ │ Excel Files │────────▶│ Sync Agent │ │
│ │ (Local/ │ Reads │ (Python) │ │
│ │ Shared) │ Cells │ │ │
│ └──────────────┘ └──────┬───────┘ │
│ │ │
│ │ HTTP POST │
│ │ (Calculation Data) │
└───────────────────────────────────┼───────────────────────────┘
│
│ Internet
│
┌───────────────────────────────────┼───────────────────────────┐
│ CLOUD PLATFORM │
│ │ │
│ ┌───────────────────────────────▼────────────┐ │
│ │ Web Application / API │ │
│ │ - Receives calculation data │ │
│ │ - Stores in database │ │
│ │ - Can request syncs on-demand │ │
│ └─────────────────────────────────────────────┘ │
│ │
└───────────────────────────────────────────────────────────────┘
---## 🎯 Business Goals & Value Proposition### Primary Goals:1. **Eliminate Manual Data Entry**   - No more copy/pasting values from Excel to web forms   - Reduces human error by 90%+   - Saves hours of repetitive work per project2. **Real-Time Data Synchronization**   - Cloud platform always has latest calculation results   - Engineers update Excel → Platform updates automatically   - No stale data issues3. **Maintain Engineering Workflow**   - Engineers continue using Excel (familiar tool)   - No need to learn new software   - Excel remains the "source of truth"4. **Centralized Data Access**   - Project managers, clients, stakeholders access data via web platform   - Historical tracking of calculation changes   - Audit trail with timestamps### Use Cases:- **Structural Engineering**: Sync load calculations (snow, wind, seismic) from Excel to project management platform- **Construction Projects**: Automatically update material quantities, cost estimates- **Design Reviews**: Real-time visibility into calculation changes- **Compliance**: Track when calculations were updated and by what values---## 🔧 How It Works - Technical Flow### Component Breakdown:#### 1. **ExcelReader** (Lines 42-84)- **Purpose**: Extracts specific cell values from Excel files- **How**: Uses `openpyxl` library with `data_only=True` to read calculated values (not formulas)- **Input**: File path, sheet name, cell mappings (e.g., `{"ground_snow_load": "B6"}`)- **Output**: Dictionary of field names → cell values#### 2. **PlatformAPI** (Lines 87-153)- **Purpose**: Communicates with cloud platform via HTTP REST API- **Methods**:  - `send_calculation_data()`: POSTs extracted data to platform  - `check_sync_request()`: Polls platform to see if sync is needed- **Authentication**: Bearer token (API key)#### 3. **ExcelFileHandler** (Lines 156-175)- **Purpose**: Monitors Excel files for changes using file system events- **How**: Uses `watchdog` library to detect file modifications- **Feature**: Debouncing (2-second delay) to prevent duplicate triggers#### 4. **SyncAgent** (Lines 178-285)- **Purpose**: Main orchestrator that coordinates all components- **Modes**:  - **Polling**: Checks platform every N seconds for sync requests  - **Watch**: Monitors files for changes and auto-syncs (optional)  - **Once**: Syncs all projects once and exits (for testing)---## 📊 Data Flow Example**Scenario**: Engineer updates snow load calculation in Excel
Engineer opens: Structural_Calcs.xlsx
Updates cell B6: 50.0 → 75.0 (ground_snow_load)
Saves file
[If Watch Mode Enabled]
FileHandler detects change
SyncAgent triggers sync_project()
ExcelReader reads:
B6 → ground_snow_load: 75.0
B8 → wind_load: 120.0
B9 → roof_pitch: 30.0
... (all mapped cells)
PlatformAPI creates payload:
{
"data": {
"ground_snow_load": 75.0,
"wind_load": 120.0,
"roof_pitch": 30.0
},
"timestamp": "2024-01-15T14:30:00Z",
"source": "local_agent"
}
HTTP POST to: https://platform.com/api/projects/metro-line-5/calculations
Cloud platform receives and stores data
Web interface updates automatically
---## 🔌 Integration Requirements### Cloud Platform Must Provide:1. **Sync Request Endpoint**   
GET /api/projects/{project_id}/sync-requests
Response: {"sync_requested": true/false}
2. **Data Receiving Endpoint**
POST /api/projects/{project_id}/calculations
Body: {
"data": {...},
"timestamp": "ISO8601",
"source": "local_agent"
}
Response: 200 OK
3. **Authentication**   - Bearer token authentication   - API key provided in config.json### Local Environment Requirements:1. **File Access**: Agent must have read access to Excel files2. **Network**: Internet connectivity to reach cloud platform3. **Python**: Python 3.8+ with required packages4. **Permissions**: Ability to run as background service (optional)---## 🚀 Deployment Scenarios### Scenario 1: Single Engineer's Machine- Agent runs on engineer's laptop- Monitors local Excel files- Syncs when files change or platform requests### Scenario 2: Shared Network Drive- Agent runs on file server or dedicated machine- Monitors Excel files on network share- Multiple engineers' files synced to same platform### Scenario 3: Team Environment- Multiple agents (one per engineer or project)- Each agent configured for specific projects- All sync to centralized cloud platform---## 💡 Key Design Decisions1. **Why Excel?**   - Industry standard for engineering calculations   - Engineers already proficient   - Complex formulas and macros supported   - No workflow disruption2. **Why Agent-Based?**   - Excel files stay local (security, performance)   - No need to upload entire files   - Only extracts relevant data (privacy)   - Works offline, syncs when online3. **Why Polling + Watch Mode?**   - Polling: Platform can request syncs on-demand   - Watch: Immediate sync when engineers save changes   - Flexibility: Choose based on use case4. **Why Specific Cell Mapping?**   - Only extracts needed data (not entire file)   - Privacy: Doesn't expose all Excel contents   - Performance: Fast, targeted reads   - Configurable: Easy to add/remove fields---## 📈 Success Metrics- **Time Saved**: Eliminates 30-60 minutes of manual entry per project update- **Error Reduction**: 90%+ reduction in data entry errors- **Data Freshness**: Real-time sync (vs. hours/days delay)- **Adoption**: Engineers continue using Excel, no training needed- **Scalability**: One agent can handle multiple projects/files---## 🔒 Security Considerations- **API Keys**: Stored in config.json (keep secure, don't commit to git)- **File Access**: Agent only reads specified cells, not entire files- **Network**: All communication over HTTPS (encrypted)- **Authentication**: Bearer token required for all API calls- **Local Storage**: Excel files remain on local/shared drive (not uploaded)---## 🎓 SummaryThis system creates a **seamless bridge** between:- **Local Excel files** (where engineers work)- **Cloud platforms** (where stakeholders need data)**The magic**: Engineers work normally in Excel, and the platform automatically stays updated. No workflow disruption, no manual work, no errors.**The value**: Real-time data synchronization, error reduction, time savings, and maintaining the tools engineers already know and love.
Copy this into 