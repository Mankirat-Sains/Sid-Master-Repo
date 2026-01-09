interface Project {
  id: string
  name: string
  description?: string
}

interface Model {
  id: string
  name: string
  projectId: string
}

export const useSpeckle = () => {
  const config = useRuntimeConfig()

  async function searchSpeckleProjects(query: string): Promise<Project[]> {
    const graphqlQuery = `
      query SearchProjects($query: String!) {
        projects(query: $query, limit: 10) {
          items {
            id
            name
            description
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
          variables: { query }
        }
      })

      const data = response as {
        data?: {
          projects?: {
            items?: Project[]
          }
        }
      }

      return data.data?.projects?.items || []
    } catch (error) {
      console.error('Error searching projects:', error)
      return []
    }
  }

  async function getProjectModels(projectId: string): Promise<Model[]> {
    const graphqlQuery = `
      query GetProjectModels($projectId: String!) {
        project(id: $projectId) {
          models(limit: 50) {
            items {
              id
              name
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
          variables: { projectId }
        }
      })

      const data = response as {
        data?: {
          project?: {
            models?: {
              items?: Array<{ id: string; name: string }>
            }
          }
        }
      }

      const models = data.data?.project?.models?.items || []
      return models.map((m) => ({
        id: m.id,
        name: m.name,
        projectId
      }))
    } catch (error) {
      console.error('Error fetching models:', error)
      return []
    }
  }

  async function findProjectByKey(projectKey: string): Promise<Project | null> {
    // Static overrides for known project key → Speckle project ID mappings.
    // Add to this map as more projects become available in Speckle.
    const projectOverrides: Record<string, Project> = {
      // Demo fallback: maps common project keys to a known Speckle project that has models.
      '25-01-005': { id: 'bde23c9150', name: 'Demo Project (25-01-005)', description: '' },
      '25-01-011': { id: 'bde23c9150', name: 'Demo Project (25-01-011)', description: '' },
      '25-01-012': { id: 'bde23c9150', name: 'Demo Project (25-01-012)', description: '' },
      '25-01-017': { id: 'bde23c9150', name: 'Demo Project (25-01-017)', description: '' },
      '25-01-039': { id: 'bde23c9150', name: 'Demo Project (25-01-039)', description: '' },
      '25-01-105': { id: 'bde23c9150', name: 'Demo Project (25-01-105)', description: '' }
    }

    if (projectOverrides[projectKey]) {
      return projectOverrides[projectKey]
    }

    const graphqlQuery = `
      query FindProjectByName($projectName: String!) {
        activeUser {
          projects(filter: { search: $projectName }, limit: 25) {
            items {
              id
              name
              description
            }
            totalCount
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
          variables: { projectName: projectKey }
        }
      })

      const data = response as {
        data?: {
          activeUser?: {
            projects?: {
              items?: Project[]
            }
          }
        }
      }

      // Find project whose name contains the project key (e.g., "(25-01-006)")
      const projects = data.data?.activeUser?.projects?.items || []
      const matchingProject = projects.find(p => 
        p.name.includes(`(${projectKey})`) || p.name.includes(projectKey)
      )
      
      return matchingProject || null
    } catch (error) {
      console.error('Error finding project by key:', error)
      return null
    }
  }

  return {
    searchSpeckleProjects,
    getProjectModels,
    findProjectByKey
  }
}
