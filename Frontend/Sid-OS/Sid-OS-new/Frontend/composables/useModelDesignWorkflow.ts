/**
 * Model Design Workflow Composable
 * Handles the bridge design workflow logic
 */

export interface ProjectParameter {
  span?: number | null
  client?: string | null
  location?: string | null
  trafficType?: string | null
  bridgeType?: string | null
  confirmed?: boolean
}

export interface SimilarProject {
  name: string
  projectId: string
  modelId: string
  url: string
  span?: number
  bridgeType?: string
  reason?: string
}

export interface ModelDesignState {
  step: 'initial' | 'asking_questions' | 'confirmed' | 'projects_found' | 'model_created' | 'mto_shown'
  parameters: ProjectParameter
  projects?: SimilarProject[]
}

export function extractSpanRequirement(message: string): number | null {
  const spanMatch = message.match(/(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m\b)/i)
  if (spanMatch) {
    return parseFloat(spanMatch[1])
  }
  return null
}

export function determineQuestions(parameters: ProjectParameter): string[] {
  const questions: string[] = []
  
  if (!parameters.client) {
    questions.push('Who is the client for this project?')
  }
  
  if (!parameters.location) {
    questions.push('Where is this project located?')
  }
  
  if (!parameters.trafficType) {
    questions.push('What type of traffic will this bridge handle? (e.g., pedestrian, vehicular, rail)')
  }
  
  return questions
}

export function extractParameters(message: string, currentParams: ProjectParameter): Partial<ProjectParameter> {
  const lower = message.toLowerCase()
  const extracted: Partial<ProjectParameter> = {}
  
  // Extract client
  const clientPatterns = [
    /(?:client is|client:|for)\s+(?:the\s+)?([^.,!?]+(?:city|municipality|corporation|inc\.?|ltd\.?|company|firm))/i,
    /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is\s+)?the\s+client/i
  ]
  
  for (const pattern of clientPatterns) {
    const match = message.match(pattern)
    if (match && match[1]) {
      extracted.client = match[1].trim()
      break
    }
  }
  
  // Extract location
  const locationPatterns = [
    /(?:located|location is|in)\s+(?:the\s+)?(?:city\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/,
    /(?:city|location):\s*([^.,!?]+)/i
  ]
  
  for (const pattern of locationPatterns) {
    const match = message.match(pattern)
    if (match && match[1]) {
      extracted.location = match[1].trim()
      break
    }
  }
  
  // Extract traffic type
  if (lower.includes('pedestrian') || lower.includes('walking') || lower.includes('foot')) {
    extracted.trafficType = 'pedestrian'
  } else if (lower.includes('vehicular') || lower.includes('vehicle') || lower.includes('car') || lower.includes('traffic')) {
    extracted.trafficType = 'vehicular'
  } else if (lower.includes('rail') || lower.includes('train')) {
    extracted.trafficType = 'rail'
  }
  
  // Extract bridge type
  if (lower.includes('arch')) {
    extracted.bridgeType = 'arch bridge'
  } else if (lower.includes('beam')) {
    extracted.bridgeType = 'beam bridge'
  } else if (lower.includes('suspension')) {
    extracted.bridgeType = 'suspension bridge'
  } else if (lower.includes('cable')) {
    extracted.bridgeType = 'cable-stayed bridge'
  }
  
  return extracted
}

export async function searchSimilarProjects(span: number, parameters: ProjectParameter): Promise<SimilarProject[]> {
  // Simulate async processing
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // Hardcoded projects for demo
  return [
    {
      name: '2025-07-005 ABC Consulting Trout Lake',
      projectId: 'bde23c9150',
      modelId: 'aecd335026',
      url: 'https://app.speckle.systems/projects/bde23c9150/models/aecd335026',
      span: 10,
      reason: 'Similar span coverage and design requirements'
    },
    {
      name: '2025-02-089 Windsor Trail crossing',
      projectId: 'bde23c9150',
      modelId: '13b0f5b797',
      url: 'https://app.speckle.systems/projects/bde23c9150/models/13b0f5b797',
      span: 12,
      reason: 'Matching span and structural approach'
    },
    {
      name: '2025-01-078 Algonquin Park',
      projectId: 'bde23c9150',
      modelId: 'fc47277266',
      url: 'https://app.speckle.systems/projects/bde23c9150/models/fc47277266',
      span: 10,
      reason: 'Appropriate span coverage with similar loading conditions'
    }
  ]
}

export async function createModel(span: number, bridgeType: string, parameters: ProjectParameter): Promise<SimilarProject> {
  // Simulate async processing
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // Hardcoded new project for demo
  return {
    name: `New ${bridgeType} - ${span}m span`,
    projectId: 'bde23c9150',
    modelId: 'df5a6a178c',
    url: 'https://app.speckle.systems/projects/bde23c9150/models/df5a6a178c',
    span,
    bridgeType
  }
}

export const useModelDesignWorkflow = () => {
  return {
    extractSpanRequirement,
    determineQuestions,
    extractParameters,
    searchSimilarProjects,
    createModel
  }
}
