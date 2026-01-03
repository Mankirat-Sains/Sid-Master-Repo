# SidOS - Engineering Operating System

A unified, demo-ready UI application that integrates three existing systems into one cohesive platform for construction/BIM project management.

## Features

### 1. BIM Model Viewer & Query Interface
- Integrates Speckle 3D viewer component
- Connects to GraphQL API at AWS endpoint
- Allows users to:
  - Load and visualize BIM models
  - Query BIM data (properties, elements, relationships)
  - Ask natural language questions about the model via AI

### 2. Document Intelligence (RAG)
- Interface to query PDFs and technical drawings
- Connects to Supabase backend from rag-GHD-Demo
- Features:
  - Document upload/selection
  - Natural language question input
  - AI-generated responses with source citations
  - Visual display of relevant drawing sections

### 3. Employee Tracking Dashboard
- Adapts the v0-employee-tracking UI
- Displays:
  - Team member status/availability
  - Current project assignments
  - Activity timelines or task completion
  - Resource allocation visualizations
- Uses dummy/mock data for demo purposes

### 4. Unified Command Center
- Dashboard overview showing:
  - Recent BIM queries
  - Document analysis activity
  - Team productivity metrics
  - Quick action buttons for common workflows

## Tech Stack

- **Frontend Framework**: Nuxt 4 (Vue 3)
- **UI Framework**: Tailwind CSS
- **3D Viewer**: @speckle/viewer
- **Backend Integration**: 
  - FastAPI (RAG system)
  - Speckle GraphQL API
  - Supabase (vector database)

## Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
cd Frontend
npm install
```

2. Create `.env` file in the `Frontend` directory:
```env
# RAG Backend API
ORCHESTRATOR_URL=http://localhost:8000
# or
RAG_API_URL=http://localhost:8000

# Speckle Server
SPECKLE_URL=http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com
# or
SPECKLE_SERVER_URL=http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com

# Speckle Authentication Token (if required)
SPECKLE_TOKEN=your_token_here
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Project Structure

```
Frontend/
├── components/
│   ├── tabs/              # Tab components for each main section
│   │   ├── BimViewerTab.vue
│   │   ├── DocumentIntelligenceTab.vue
│   │   ├── EmployeeTrackingTab.vue
│   │   └── OverviewTab.vue
│   ├── ChatInterface.vue        # Main chat interface for BIM queries
│   ├── DocumentChatInterface.vue # Document RAG chat interface
│   ├── SpeckleViewer.vue        # Speckle 3D viewer wrapper
│   ├── EmployeeCard.vue         # Employee card component
│   └── TimeScaleToggle.vue      # Time scale toggle component
├── composables/
│   ├── useChat.ts        # Chat API integration
│   ├── useViewer.ts      # Speckle viewer utilities
│   └── useSpeckle.ts     # Speckle GraphQL queries
├── data/
│   └── employees.ts      # Mock employee data
├── pages/
│   └── index.vue         # Main application page with tabs
└── nuxt.config.ts        # Nuxt configuration
```

## Integration Details

### RAG Backend Integration

The RAG backend should be running on the port specified in `ORCHESTRATOR_URL`. The backend provides a `/chat` endpoint that accepts:
- `message`: User's question
- `session_id`: Session identifier
- `images_base64`: Optional array of base64-encoded images

### Speckle Integration

The Speckle viewer integrates with the AWS-hosted Speckle server. Authentication may be required depending on server configuration. The viewer uses:
- GraphQL API for project/model queries
- ObjectLoader for loading 3D model data
- Viewer for rendering 3D models

### Employee Tracking

The employee tracking dashboard uses mock data from `data/employees.ts`. For production, this should be replaced with actual API calls to an employee management system.

## Demo Script

1. **Start with Overview Tab**: Show the unified command center
2. **BIM Viewer**: 
   - Query a project (e.g., "Show me project 25-08-127")
   - Demonstrate 3D model loading and navigation
   - Show BIM data queries
3. **Document Intelligence**:
   - Ask questions about technical drawings
   - Show AI responses with citations
4. **Employee Dashboard**:
   - Show team productivity metrics
   - Demonstrate filtering and time scale toggles
5. **Highlight Integration**: Show how all pieces work together

## Development Notes

- The application uses Vue 3 Composition API
- TypeScript is enabled with strict mode
- Tailwind CSS is used for styling
- All components are designed to be responsive

## Troubleshooting

### Speckle Viewer Not Loading
- Check that `SPECKLE_URL` is correctly set
- Verify network connectivity to AWS endpoint
- Check browser console for CORS or authentication errors

### RAG Backend Connection Issues
- Ensure the RAG backend is running
- Verify `ORCHESTRATOR_URL` matches the backend port
- Check CORS settings on the backend

### Employee Data Not Showing
- Verify `data/employees.ts` is properly imported
- Check browser console for any TypeScript errors

## License

Internal use only - Demo application
