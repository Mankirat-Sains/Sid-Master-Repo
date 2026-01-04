import { Viewer } from '@speckle/viewer'
import { ObjectLoader } from '@speckle/objectloader2'

interface LoadModelParams {
  projectId: string
  modelId: string
  commitId?: string
  serverUrl: string
  token: string
}

export const useViewer = () => {
  async function loadModel(viewer: Viewer, params: LoadModelParams): Promise<void> {
    const { projectId, modelId, commitId, serverUrl, token } = params

    try {
      // Get the latest commit if not specified
      let commitIdToUse = commitId
      if (!commitIdToUse) {
        // Query GraphQL for latest commit
        const commit = await getLatestCommit(serverUrl, token, projectId, modelId)
        commitIdToUse = commit?.id
      }

      if (!commitIdToUse) {
        throw new Error('No commit found for model')
      }

      // Load objects using ObjectLoader
      const loader = new ObjectLoader({
        serverUrl,
        token,
        streamId: projectId,
        objectId: commitIdToUse
      })

      // Load all objects
      const objects = await loader.getAndConstructAll()

      // Clear existing scene
      viewer.reset()

      // Add objects to viewer
      for (const obj of objects) {
        viewer.addObject(obj)
      }

      // Fit to view
      viewer.requestRender()
      await new Promise((resolve) => setTimeout(resolve, 100))
      viewer.cameraHandler.zoomExtents()
    } catch (error) {
      console.error('Error loading model:', error)
      throw error
    }
  }

  async function getLatestCommit(
    serverUrl: string,
    token: string,
    projectId: string,
    modelId: string
  ): Promise<{ id: string } | null> {
    const query = `
      query GetLatestCommit($projectId: String!, $modelId: String!) {
        project(id: $projectId) {
          model(id: $modelId) {
            versions(limit: 1) {
              items {
                id
                referencedObject
              }
            }
          }
        }
      }
    `

    try {
      const response = await $fetch(`${serverUrl}/graphql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: {
          query,
          variables: {
            projectId,
            modelId
          }
        }
      })

      const data = response as {
        data?: {
          project?: {
            model?: {
              versions?: {
                items?: Array<{ id: string; referencedObject: string }>
              }
            }
          }
        }
      }

      const commit = data.data?.project?.model?.versions?.items?.[0]
      return commit ? { id: commit.referencedObject } : null
    } catch (error) {
      console.error('Error fetching commit:', error)
      return null
    }
  }

  return {
    loadModel
  }
}

