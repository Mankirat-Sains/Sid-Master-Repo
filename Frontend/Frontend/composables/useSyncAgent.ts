/**
 * Composable for Excel Sync Agent operations
 * Provides functions to interact with the Excel Sync Agent via the main backend
 */

interface SyncStatus {
  status: string
  last_sync: string | null
  active_projects: string[]
  errors: string[]
  agent_configured: boolean
}

interface ProjectInfo {
  project_id: string
  project_name: string
  excel_file: string
  sheet_name: string
  cell_mappings: Record<string, string>
  last_synced: string | null
  file_exists: boolean
}

interface SyncResult {
  success: boolean
  project_id: string
  message: string
  data?: Record<string, unknown>
  timestamp: string
}

interface SyncHistory {
  history: Array<{
    project_id: string
    success: boolean
    message: string
    data?: Record<string, unknown>
    timestamp: string
  }>
  total: number
}

interface ProjectData {
  project_id: string
  data: Record<string, unknown>
  timestamp: string
}

export const useSyncAgent = () => {
  const config = useRuntimeConfig()

  /**
   * Get the current status of the Excel Sync Agent
   */
  async function getStatus(): Promise<SyncStatus> {
    const url = `${config.public.orchestratorUrl}/api/agent/status`
    
    try {
      const response = await $fetch<SyncStatus>(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      return response
    } catch (error: any) {
      console.error('❌ Error getting agent status:', error)
      throw new Error(`Failed to get agent status: ${error.message || 'Unknown error'}`)
    }
  }

  /**
   * Get list of all configured projects
   */
  async function getProjects(): Promise<ProjectInfo[]> {
    const url = `${config.public.orchestratorUrl}/api/agent/projects`
    
    try {
      const response = await $fetch<ProjectInfo[]>(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      return response
    } catch (error: any) {
      console.error('❌ Error getting agent projects:', error)
      throw new Error(`Failed to get agent projects: ${error.message || 'Unknown error'}`)
    }
  }

  /**
   * Trigger a sync for a specific project or all projects
   * @param projectId - Optional project ID. If not provided, syncs all projects
   * @param force - Whether to force sync even if not requested
   */
  async function triggerSync(projectId?: string, force: boolean = false): Promise<SyncResult> {
    const url = `${config.public.orchestratorUrl}/api/agent/sync`
    
    try {
      const response = await $fetch<SyncResult>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          project_id: projectId || null,
          force
        }
      })
      
      console.log('✅ Sync triggered:', response)
      return response
    } catch (error: any) {
      console.error('❌ Error triggering sync:', error)
      throw new Error(`Failed to trigger sync: ${error.message || 'Unknown error'}`)
    }
  }

  /**
   * Get sync history
   * @param limit - Maximum number of history entries to return (default: 50)
   */
  async function getHistory(limit: number = 50): Promise<SyncHistory> {
    const url = `${config.public.orchestratorUrl}/api/agent/history`
    
    try {
      const response = await $fetch<SyncHistory>(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        params: {
          limit
        }
      })
      
      return response
    } catch (error: any) {
      console.error('❌ Error getting sync history:', error)
      throw new Error(`Failed to get sync history: ${error.message || 'Unknown error'}`)
    }
  }

  /**
   * Get current data from a project's Excel file without syncing
   * @param projectId - Project ID to get data for
   */
  async function getProjectData(projectId: string): Promise<ProjectData> {
    const url = `${config.public.orchestratorUrl}/api/agent/project/${projectId}/data`
    
    try {
      const response = await $fetch<ProjectData>(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      return response
    } catch (error: any) {
      console.error('❌ Error getting project data:', error)
      throw new Error(`Failed to get project data: ${error.message || 'Unknown error'}`)
    }
  }

  /**
   * Configure the agent with a new configuration
   * @param config - Agent configuration object
   */
  async function configureAgent(config: {
    platform_url: string
    api_key: string
    poll_interval?: number
    auto_sync_on_change?: boolean
    projects: Array<{
      project_id: string
      project_name: string
      excel_file: string
      sheet_name: string
      cell_mappings: Record<string, string>
    }>
  }): Promise<{ status: string; projects_count: number; message: string }> {
    const url = `${config.public.orchestratorUrl}/api/agent/configure`
    
    try {
      const response = await $fetch<{ status: string; projects_count: number; message: string }>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: config
      })
      
      console.log('✅ Agent configured:', response)
      return response
    } catch (error: any) {
      console.error('❌ Error configuring agent:', error)
      throw new Error(`Failed to configure agent: ${error.message || 'Unknown error'}`)
    }
  }

  return {
    getStatus,
    getProjects,
    triggerSync,
    getHistory,
    getProjectData,
    configureAgent
  }
}
