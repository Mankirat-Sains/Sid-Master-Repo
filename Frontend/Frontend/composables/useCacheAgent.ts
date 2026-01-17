/**
 * Composable for interacting with the cache generation API
 */
import { useRuntimeConfig } from '#app'

interface BuildCacheRequest {
  folder_path: string
}

interface BuildCacheResponse {
  success: boolean
  project_id?: string
  message: string
  cache_location?: string
  total_files?: number
  processed?: number
  failed?: number
  timestamp: string
}

interface CacheStatus {
  exists: boolean
  project_id: string
  folder_path?: string
  created_at?: string
  total_files?: number
  processed?: number
  failed?: number
  cache_location?: string
  files?: Array<{
    file_path: string
    file_hash: string
    file_name: string
    file_type: string
    cached_at: string
  }>
  message?: string
}

export const useCacheAgent = () => {
  const config = useRuntimeConfig()

  /**
   * Get the agent API URL
   */
  const getAgentApiUrl = () => {
    return config.public.agentApiUrl || 'http://localhost:8001'
  }

  /**
   * Build cache for a project folder
   * This triggers cache generation in the background
   */
  async function buildCache(folderPath: string): Promise<BuildCacheResponse> {
    const url = `${getAgentApiUrl()}/api/agent/cache/build`
    
    try {
      const response = await $fetch<BuildCacheResponse>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          folder_path: folderPath
        }
      })
      
      console.log('✅ Cache build started:', response)
      return response
    } catch (error: any) {
      console.error('❌ Error starting cache build:', error)
      throw new Error(`Failed to start cache build: ${error.data?.detail || error.message || 'Unknown error'}`)
    }
  }

  /**
   * Get cache status for a project
   */
  async function getCacheStatus(projectId: string): Promise<CacheStatus> {
    const url = `${getAgentApiUrl()}/api/agent/cache/status/${encodeURIComponent(projectId)}`
    
    try {
      const response = await $fetch<CacheStatus>(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      return response
    } catch (error: any) {
      console.error('❌ Error getting cache status:', error)
      // Return a status indicating cache doesn't exist
      return {
        exists: false,
        project_id: projectId,
        message: error.data?.detail || error.message || 'Cache not found'
      }
    }
  }

  /**
   * Poll cache status until it's complete or timeout
   */
  async function waitForCache(
    projectId: string,
    options: {
      interval?: number // milliseconds between checks
      timeout?: number // maximum time to wait
      onProgress?: (status: CacheStatus) => void
    } = {}
  ): Promise<CacheStatus> {
    const interval = options.interval || 2000 // Check every 2 seconds
    const timeout = options.timeout || 300000 // 5 minutes max
    const startTime = Date.now()

    while (Date.now() - startTime < timeout) {
      const status = await getCacheStatus(projectId)
      
      if (options.onProgress) {
        options.onProgress(status)
      }

      // If cache exists and processing is complete
      if (status.exists) {
        const total = status.total_files || 0
        const processed = status.processed || 0
        const failed = status.failed || 0
        
        // If all files are processed (or failed), we're done
        if (processed + failed >= total && total > 0) {
          return status
        }
      }

      // Wait before next check
      await new Promise(resolve => setTimeout(resolve, interval))
    }

    // Timeout - return current status
    return await getCacheStatus(projectId)
  }

  return {
    buildCache,
    getCacheStatus,
    waitForCache
  }
}
