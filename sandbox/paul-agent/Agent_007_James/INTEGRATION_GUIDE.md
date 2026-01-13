# Excel Sync Agent - Frontend Integration Guide

This guide explains how to use the Excel Sync Agent with the frontend through the main backend.

## Architecture Overview

```
Frontend (Nuxt.js)
    ↓ HTTP calls
Main Backend (api_server.py, port 8000)
    ↓ Proxies to
Agent API Service (agent_api.py, port 8001)
    ↓ Monitors/Syncs
Excel Files (local machine)
```

## Setup Instructions

### 1. Install Agent Dependencies

```bash
cd /Volumes/J/Sid-Master-Repo/sandbox/paul-agent/Agent_007_James
pip install -r requirements.txt
```

### 2. Configure the Agent

Create a `config.json` file (see `config.example.json` for reference):

```json
{
  "platform_url": "https://your-platform.com",
  "api_key": "your-api-key-here",
  "poll_interval": 30,
  "auto_sync_on_change": false,
  "projects": [
    {
      "project_id": "metro-line-5",
      "project_name": "Metro Line 5 Extension",
      "excel_file": "/path/to/Structural_Calcs.xlsx",
      "sheet_name": "INFO",
      "cell_mappings": {
        "ground_snow_load": "B6",
        "wind_load": "B8"
      }
    }
  ]
}
```

### 3. Start the Agent API Service

```bash
cd /Volumes/J/Sid-Master-Repo/sandbox/paul-agent/Agent_007_James
python agent_api.py --config config.json --port 8001
```

The agent service will run on `http://localhost:8001`

### 4. Configure Main Backend (Optional)

The main backend is already configured to connect to the agent service at `http://localhost:8001`.

If you need to change the agent URL, set the environment variable:

```bash
export AGENT_API_URL=http://localhost:8001
```

Or add it to your `.env` file in the Backend directory.

### 5. Start the Main Backend

```bash
cd /Volumes/J/Sid-Master-Repo/Backend
python api_server.py
```

The main backend will run on `http://localhost:8000`

### 6. Use in Frontend

The frontend composable is ready to use! Import it in your Vue components:

```vue
<script setup lang="ts">
const { getStatus, getProjects, triggerSync, getHistory } = useSyncAgent()

// Get agent status
const status = await getStatus()

// Get all projects
const projects = await getProjects()

// Trigger sync for a specific project
await triggerSync('metro-line-5')

// Trigger sync for all projects
await triggerSync()

// Get sync history
const history = await getHistory(100)
</script>
```

## API Endpoints

### Main Backend Endpoints (via orchestratorUrl)

All endpoints are available through the main backend at `http://localhost:8000`:

- `GET /api/agent/status` - Get agent status
- `GET /api/agent/projects` - Get list of projects
- `POST /api/agent/sync` - Trigger sync
- `GET /api/agent/history` - Get sync history
- `GET /api/agent/project/{project_id}/data` - Get project data
- `POST /api/agent/configure` - Configure agent

### Direct Agent API Endpoints (port 8001)

You can also call the agent service directly:

- `GET /health` - Health check
- `GET /api/agent/status` - Status
- `GET /api/agent/projects` - Projects
- `POST /api/agent/sync` - Trigger sync
- `GET /api/agent/history` - History
- `POST /api/agent/configure` - Configure

## Frontend Usage Examples

### Example 1: Display Agent Status

```vue
<template>
  <div>
    <h2>Excel Sync Agent</h2>
    <div v-if="status">
      <p>Status: {{ status.status }}</p>
      <p>Last Sync: {{ status.last_sync || 'Never' }}</p>
      <p>Active Projects: {{ status.active_projects.length }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getStatus } = useSyncAgent()
const status = ref<SyncStatus | null>(null)

onMounted(async () => {
  try {
    status.value = await getStatus()
  } catch (error) {
    console.error('Failed to get status:', error)
  }
})
</script>
```

### Example 2: List Projects and Trigger Sync

```vue
<template>
  <div>
    <h2>Projects</h2>
    <div v-for="project in projects" :key="project.project_id">
      <h3>{{ project.project_name }}</h3>
      <p>File: {{ project.excel_file }}</p>
      <p>Last Synced: {{ project.last_synced || 'Never' }}</p>
      <button @click="syncProject(project.project_id)">
        Sync Now
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getProjects, triggerSync } = useSyncAgent()
const projects = ref<ProjectInfo[]>([])

onMounted(async () => {
  try {
    projects.value = await getProjects()
  } catch (error) {
    console.error('Failed to get projects:', error)
  }
})

async function syncProject(projectId: string) {
  try {
    const result = await triggerSync(projectId)
    console.log('Sync result:', result)
    // Refresh projects to get updated last_synced
    projects.value = await getProjects()
  } catch (error) {
    console.error('Failed to sync:', error)
  }
}
</script>
```

### Example 3: Display Sync History

```vue
<template>
  <div>
    <h2>Sync History</h2>
    <div v-for="entry in history.history" :key="entry.timestamp">
      <p>
        {{ entry.project_id }} - 
        {{ entry.success ? '✅' : '❌' }} - 
        {{ entry.message }} - 
        {{ new Date(entry.timestamp).toLocaleString() }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getHistory } = useSyncAgent()
const history = ref<SyncHistory | null>(null)

onMounted(async () => {
  try {
    history.value = await getHistory(50)
  } catch (error) {
    console.error('Failed to get history:', error)
  }
})
</script>
```

## Troubleshooting

### Agent service not reachable

If you see "Agent service not reachable" errors:

1. Make sure the agent API service is running:
   ```bash
   python agent_api.py --config config.json --port 8001
   ```

2. Check that the agent service is accessible:
   ```bash
   curl http://localhost:8001/health
   ```

3. Verify the `AGENT_API_URL` environment variable matches the agent service URL

### Agent not configured

If you see "Agent not configured" errors:

1. Make sure you've created a `config.json` file
2. Start the agent service with the `--config` flag
3. Or use the `/api/agent/configure` endpoint to configure it dynamically

### Excel file not found

If you see "Excel file not found" errors:

1. Check that the file paths in `config.json` are correct
2. Make sure the agent service has read permissions for the Excel files
3. Use absolute paths in the configuration

## Next Steps

- Add UI components for sync dashboard
- Implement real-time sync status updates (WebSocket)
- Add sync scheduling functionality
- Create sync history visualization
- Add error notifications and alerts
