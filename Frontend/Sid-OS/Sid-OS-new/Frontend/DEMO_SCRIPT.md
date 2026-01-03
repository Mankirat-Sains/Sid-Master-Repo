# SidOS Demo Script

This script outlines the recommended flow for demonstrating SidOS during a lunch-and-learn presentation.

## Pre-Demo Setup

1. **Start RAG Backend** (if running locally):
   ```bash
   cd rag-GHD-Demo/rag-waddell/RAG/Backend
   python api_server.py
   ```

2. **Start SidOS Frontend**:
   ```bash
   cd SidOS/Frontend
   npm run dev
   ```

3. **Verify Connections**:
   - Check that RAG backend is accessible at configured URL
   - Verify Speckle server is accessible (AWS endpoint)
   - Ensure browser can load the application

## Demo Flow (15-20 minutes)

### 1. Introduction - Command Center (2 minutes)

**Start at Overview Tab**

- "This is SidOS - a unified platform that brings together three powerful systems for construction/BIM project management"
- Point out the **Command Center** showing:
  - Recent activity feed
  - Quick stats (BIM queries, document analysis)
  - Team productivity summary
  - Quick action buttons

**Key Talking Points:**
- "All your tools in one place"
- "Real-time insights across all systems"

---

### 2. BIM Viewer & Query Interface (5 minutes)

**Navigate to BIM Viewer Tab**

**Step 1: Query a Project**
- Type in chat: "Show me project 25-08-127" or "What can you tell me about the Beef Barn Parlour Addition?"
- Demonstrate:
  - Natural language query
  - AI response generation
  - Automatic model loading

**Step 2: Explore 3D Model**
- Once model loads in viewer:
  - Show 3D navigation (zoom, pan, rotate)
  - Use viewer controls (zoom fit, zoom in/out)
  - Point out structural elements

**Step 3: Query BIM Data**
- Ask: "What are the structural elements in this model?"
- "What materials are used in the foundation?"
- Show AI responses with BIM data

**Key Talking Points:**
- "Ask questions in natural language"
- "Seamless integration with Speckle 3D viewer"
- "Query BIM data directly from the model"

---

### 3. Document Intelligence (RAG) (4 minutes)

**Navigate to Document Intelligence Tab**

**Step 1: Document Query**
- Type: "What are the foundation requirements for project 25-04-147?"
- Or: "Show me the roof truss bracing notes"
- Demonstrate:
  - Natural language questions
  - AI-generated responses
  - Source citations

**Step 2: Technical Drawing Queries**
- Ask about specific drawing elements
- Show how AI extracts information from PDFs and technical drawings
- Point out citation links

**Key Talking Points:**
- "Query PDFs and technical drawings using AI"
- "Get instant answers with source citations"
- "No need to manually search through documents"

---

### 4. Employee Tracking Dashboard (3 minutes)

**Navigate to Employee Tracking Tab**

**Step 1: Overview**
- Show employee cards grid
- Point out:
  - Weekly/monthly/yearly hours
  - Project breakdown
  - Role information

**Step 2: Filtering & Time Scales**
- Use search to filter employees
- Toggle between Weekly, Monthly, Yearly views
- Show how data updates dynamically

**Step 3: Productivity Metrics**
- Highlight:
  - Total team hours
  - Active projects
  - Resource allocation

**Key Talking Points:**
- "Track team productivity in real-time"
- "Understand resource allocation across projects"
- "Easy filtering and time scale views"

---

### 5. Integration Highlights (2 minutes)

**Return to Command Center**

**Highlight Integration:**
- "See how all three systems work together"
- Point out recent activity feed showing:
  - BIM queries
  - Document analysis
  - Employee tracking updates

**Quick Actions:**
- Show quick action buttons
- Demonstrate how they navigate to different sections
- Emphasize unified workflow

---

### 6. Closing (1 minute)

**Summary:**
- "SidOS brings together BIM visualization, document intelligence, and team tracking"
- "Natural language interfaces make it easy to query complex data"
- "All in one unified platform"

**Questions & Answers**

---

## Demo Tips

### Do's:
- ✅ Start with the Overview to show the big picture
- ✅ Use real project numbers that exist in your system
- ✅ Let AI responses load fully before moving on
- ✅ Show the viewer controls and 3D navigation
- ✅ Highlight the seamless integration between tabs
- ✅ Keep explanations concise and focused on value

### Don'ts:
- ❌ Don't rush through the 3D model loading
- ❌ Don't skip showing citations in document queries
- ❌ Don't forget to demonstrate the search/filter functionality
- ❌ Don't spend too long on any single feature

### Backup Plans:
- If RAG backend is slow: Have some pre-loaded responses ready
- If Speckle viewer fails: Have screenshots ready, explain the capability
- If network issues: Have a local demo mode or screenshots prepared

---

## Technical Requirements

**For Live Demo:**
- Stable internet connection (for AWS Speckle server)
- RAG backend running and accessible
- Browser with WebGL support (for 3D viewer)
- Presentation screen/projector

**For Backup:**
- Screenshots of each major feature
- Pre-recorded video walkthrough
- Local mock data mode (if available)

---

## Troubleshooting During Demo

**If something breaks:**
1. Stay calm and acknowledge the issue
2. Try refreshing the page (if appropriate)
3. Move to the next section and circle back
4. Have backup screenshots/videos ready

**Common Issues:**
- **Viewer not loading**: Check network, try a different project
- **RAG timeout**: Move to employee dashboard, come back later
- **Slow responses**: Explain that it's processing complex queries

---

## Success Criteria

By the end of the demo, audience should understand:
- ✅ SidOS unifies three powerful systems
- ✅ Natural language queries work across all features
- ✅ 3D BIM models can be queried and explored
- ✅ Documents can be intelligently searched
- ✅ Team productivity is easily trackable
- ✅ All systems work together seamlessly

---

## Next Steps

After the demo:
- Provide access/credentials if appropriate
- Share documentation
- Schedule follow-up sessions for interested users
- Collect feedback for improvements

