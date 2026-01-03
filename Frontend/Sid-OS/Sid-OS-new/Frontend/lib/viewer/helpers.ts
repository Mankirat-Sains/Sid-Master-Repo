/**
 * Helper functions for viewer operations
 */

export function parseSpeckleUrl(url: string): {
  projectId: string
  modelId: string
  commitId?: string
} | null {
  // Parse Speckle URLs like:
  // https://speckle.xyz/projects/{projectId}/models/{modelId}
  // http://localhost:3000/projects/{projectId}/models/{modelId}?version={commitId}
  
  const urlPattern = /\/projects\/([a-zA-Z0-9]+)\/models\/([a-zA-Z0-9]+)/
  const match = url.match(urlPattern)
  
  if (!match) return null

  const projectId = match[1]
  const modelId = match[2]
  
  // Try to extract commit ID from query params
  const urlObj = new URL(url)
  const commitId = urlObj.searchParams.get('version') || undefined

  return {
    projectId,
    modelId,
    commitId
  }
}

export function formatSpeckleUrl(
  serverUrl: string,
  projectId: string,
  modelId: string,
  commitId?: string
): string {
  const url = `${serverUrl}/projects/${projectId}/models/${modelId}`
  return commitId ? `${url}?version=${commitId}` : url
}

