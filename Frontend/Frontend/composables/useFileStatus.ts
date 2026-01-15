interface StreamInfo {
  id: string
  name: string
  models: Array<{ id: string; name: string }>
}

export const useFileStatus = () => {
  const config = useRuntimeConfig()

  /**
   * Find a Speckle stream by exact file name match (without extension)
   * @param fileName - Full file name (e.g., "Mark Craig 60' x 100' Shed Addition (25-01-101).rvt")
   * @returns Stream info with ID and models, or null if not found
   */
  async function findStreamByFileName(fileName: string): Promise<StreamInfo | null> {
    // Remove file extension for matching
    const nameWithoutExt = fileName.replace(/\.\w+$/, '')
    
    const graphqlQuery = `
      query FindStreamByName($searchQuery: String!) {
        activeUser {
          projects(filter: { search: $searchQuery }, limit: 100) {
            items {
              id
              name
              models(limit: 50) {
                items {
                  id
                  name
                }
              }
            }
          }
        }
      }
    `

    try {
      const response = await $fetch(`${config.public.speckleUrl}/graphql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${config.public.speckleToken}`
        },
        body: {
          query: graphqlQuery,
          variables: { searchQuery: nameWithoutExt }
        }
      })

      const data = response as {
        data?: {
          activeUser?: {
            projects?: {
              items?: Array<{
                id: string
                name: string
                models?: {
                  items?: Array<{ id: string; name: string }>
                }
              }>
            }
          }
        }
      }

      const projects = data.data?.activeUser?.projects?.items || []
      
      // Find exact match (case-insensitive)
      const matchingProject = projects.find(p => 
        p.name.toLowerCase() === nameWithoutExt.toLowerCase()
      )
      
      if (matchingProject) {
        const models = matchingProject.models?.items || []
        return {
          id: matchingProject.id,
          name: matchingProject.name,
          models: models.map(m => ({ id: m.id, name: m.name }))
        }
      }
      
      return null
    } catch (error) {
      console.error('Error finding stream by file name:', error)
      return null
    }
  }

  /**
   * Check if a file exists in the database (Speckle streams)
   * @param fileName - Full file name
   * @returns true if file exists in database, false otherwise
   */
  async function checkFileInDatabase(fileName: string): Promise<boolean> {
    const streamInfo = await findStreamByFileName(fileName)
    return streamInfo !== null
  }

  /**
   * Get stream info for a file (includes models)
   * @param fileName - Full file name
   * @returns Stream info with models, or null if not found
   */
  async function getFileStreamInfo(fileName: string): Promise<StreamInfo | null> {
    return findStreamByFileName(fileName)
  }

  return {
    findStreamByFileName,
    checkFileInDatabase,
    getFileStreamInfo
  }
}
