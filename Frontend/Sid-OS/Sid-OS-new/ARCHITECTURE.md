# SidOS Architecture Overview

## System Architecture

SidOS is built as a unified Nuxt.js (Vue 3) application that integrates three existing systems:

1. **RAG System** (rag-GHD-Demo) - Document intelligence and AI-powered queries
2. **Employee Tracking** (v0-employee-tracking) - Team productivity dashboard
3. **Speckle BIM Viewer** - 3D model visualization and query interface

## Technology Stack

### Frontend
- **Framework**: Nuxt 4 (Vue 3 with Composition API)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **3D Viewer**: @speckle/viewer
- **State Management**: Vue Composition API (refs, computed)

### Backend Integration
- **RAG API**: FastAPI (Python) - `/chat` endpoint
- **Speckle Server**: AWS-hosted GraphQL API
- **Vector Database**: Supabase (via RAG backend)

## Architecture Decision: Nuxt vs Next.js

**Decision**: Use Nuxt.js as the base framework

**Rationale**:
- Speckle viewer (`@speckle/viewer`) is designed for Nuxt/Vue ecosystem
- Better integration with Vue 3 Composition API
- Single framework approach avoids complexity of multi-framework setup

**Solution for Next.js Components**:
- Ported React components from v0-employee-tracking to Vue/Nuxt
- Converted React hooks to Vue composables
- Maintained same UI/UX patterns and data structures

## Application Structure

### Tab-Based Navigation

The application uses a tab-based interface with four main sections:

```
┌─────────────────────────────────────────┐
│           SidOS Header                  │
├─────────────────────────────────────────┤
│  [Overview] [BIM] [Documents] [Employees]│
├─────────────────────────────────────────┤
│                                         │
│         Tab Content Area                │
│                                         │
└─────────────────────────────────────────┘
```

### Component Architecture

```
pages/
  └── index.vue              # Main app with tab navigation

components/
  ├── tabs/
  │   ├── OverviewTab.vue          # Command center dashboard
  │   ├── BimViewerTab.vue         # BIM viewer + chat
  │   ├── DocumentIntelligenceTab.vue  # RAG document queries
  │   └── EmployeeTrackingTab.vue      # Team productivity
  │
  ├── ChatInterface.vue          # BIM query chat interface
  ├── DocumentChatInterface.vue  # Document RAG chat interface
  ├── SpeckleViewer.vue         # 3D model viewer wrapper
  ├── EmployeeCard.vue          # Employee card component
  └── TimeScaleToggle.vue       # Time scale selector

composables/
  ├── useChat.ts           # RAG backend API integration
  ├── useViewer.ts         # Speckle viewer utilities
  ├── useSpeckle.ts        # Speckle GraphQL queries
  └── useProjectMapping.ts # Project number to model mapping
```

## Integration Points

### 1. RAG Backend Integration

**Endpoint**: `POST /chat`

**Request**:
```typescript
{
  message: string
  session_id: string
  images_base64?: string[]
}
```

**Response**:
```typescript
{
  reply: string
  citations?: number
  model_info?: {
    projectId: string
    modelId: string
    commitId?: string
  }
}
```

**Implementation**: `composables/useChat.ts`

### 2. Speckle Viewer Integration

**Connection Flow**:
1. User queries a project via chat
2. System extracts project/model IDs from response
3. Loads 3D model using Speckle ObjectLoader
4. Renders in Viewer component

**GraphQL Queries**: `composables/useSpeckle.ts`

**Viewer Management**: `composables/useViewer.ts`

### 3. Employee Tracking

**Data Source**: Mock data from `data/employees.ts`

**Components**:
- Employee cards with time breakdowns
- Time scale toggle (weekly/monthly/yearly)
- Search/filter functionality

**Future**: Replace mock data with API calls

## Data Flow

### BIM Query Flow

```
User Input → ChatInterface
    ↓
useChat.sendChatMessage()
    ↓
RAG Backend (/chat)
    ↓
Response with model_info
    ↓
Extract project/model IDs
    ↓
Load model in SpeckleViewer
    ↓
useViewer.loadModel()
    ↓
Speckle GraphQL API
    ↓
3D Model Rendered
```

### Document Query Flow

```
User Input → DocumentChatInterface
    ↓
useChat.sendChatMessage()
    ↓
RAG Backend (/chat)
    ↓
Supabase Vector Search
    ↓
AI Response Generation
    ↓
Display with Citations
```

## Styling System

### Theme Variables

Uses Speckle's foundation color system:

```css
--foundation-page: #0a0a0a
--foundation: #111111
--foundation-2: #1a1a1a
--foundation-line: #2a2a2a
--foreground: #ffffff
--foreground-muted: #999999
--primary: #0070f3
```

### Component Styling

- Tailwind CSS utility classes
- Custom CSS variables for theming
- Consistent spacing and typography
- Dark theme optimized

## Environment Configuration

### Required Environment Variables

```env
# RAG Backend
ORCHESTRATOR_URL=http://localhost:8000

# Speckle Server
SPECKLE_URL=http://k8s-speckle-...amazonaws.com
SPECKLE_TOKEN=optional_token

# Alternative variable names supported
RAG_API_URL=
SPECKLE_SERVER_URL=
```

### Configuration Location

- `nuxt.config.ts` - Runtime config setup
- Environment variables loaded via `useRuntimeConfig()`

## Project Mapping

Project numbers (e.g., "25-08-127") are mapped to Speckle project/model IDs:

**Location**: `composables/useProjectMapping.ts`

**Usage**: ChatInterface extracts project numbers from queries and maps them to Speckle IDs for model loading.

## Error Handling

### Loading States
- All async operations show loading indicators
- Smooth transitions between states

### Error Messages
- User-friendly error messages
- Fallback UI for failed operations
- Console logging for debugging

### Network Issues
- Graceful degradation
- Retry mechanisms where appropriate
- Clear user feedback

## Performance Considerations

### Code Splitting
- Tab components loaded asynchronously
- Lazy loading for heavy components

### 3D Viewer
- Efficient model loading
- Memory management for viewer disposal
- Viewport-based optimizations

### API Calls
- Debounced search inputs
- Efficient caching where possible
- Session-based state management

## Security Considerations

### API Keys
- Environment variables only
- Never exposed to client (if applicable)
- Token-based authentication for Speckle

### CORS
- Backend must allow frontend origin
- Proper CORS headers required

## Future Enhancements

### Potential Improvements
1. **Real Employee Data**: Replace mock data with API integration
2. **Authentication**: Add user authentication system
3. **Persistence**: Save query history and preferences
4. **Advanced Filtering**: More sophisticated filtering options
5. **Real-time Updates**: WebSocket connections for live updates
6. **Mobile Responsiveness**: Enhanced mobile experience
7. **Chart Library**: Add proper charting for employee data
8. **Export Features**: Export reports and data

## Development Workflow

### Running Locally

```bash
# Frontend
cd SidOS/Frontend
npm install
npm run dev

# Backend (separate terminal)
cd rag-GHD-Demo/rag-waddell/RAG/Backend
python api_server.py
```

### Building for Production

```bash
cd SidOS/Frontend
npm run build
npm run preview
```

## Testing Strategy

### Manual Testing
- Test all three integrated systems
- Verify Speckle viewer loading
- Check RAG responses
- Validate employee data display

### Demo Testing
- Run through demo script
- Verify smooth transitions
- Check error handling
- Test with actual project data

## Troubleshooting

### Common Issues

1. **Speckle Viewer Not Loading**
   - Check SPECKLE_URL configuration
   - Verify network connectivity
   - Check browser console for errors

2. **RAG Backend Connection**
   - Verify ORCHESTRATOR_URL
   - Check backend is running
   - Verify CORS settings

3. **Employee Data Not Showing**
   - Check data/employees.ts import
   - Verify TypeScript compilation
   - Check browser console

## Conclusion

SidOS successfully integrates three disparate systems into a unified, user-friendly interface. The architecture prioritizes:

- **Simplicity**: Tab-based navigation
- **Integration**: Seamless connection between systems
- **User Experience**: Natural language interfaces
- **Scalability**: Modular component structure

The system is ready for demo and can be extended for production use.

