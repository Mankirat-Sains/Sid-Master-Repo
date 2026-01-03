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

  return {
    searchSpeckleProjects,
    getProjectModels
  }
}

