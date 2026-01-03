/**
 * Smart Chat Composable
 * Intelligently routes queries to either Speckle GraphQL API or RAG backend
 * based on query context and intent
 */

import type { ChatResponse } from './useChat'
import { useChat } from './useChat'
import { useSpeckle } from './useSpeckle'

export type ChatSource = 'speckle' | 'rag' | 'hybrid'

interface SmartChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  source?: ChatSource
  timestamp: Date
  metadata?: {
    projectId?: string
    modelId?: string
    citations?: number
    route?: string
  }
}

interface SmartChatResponse {
  message: string
  source: ChatSource
  metadata?: {
    projectId?: string
    modelId?: string
    citations?: number
    route?: string
    project_answer?: string
    code_answer?: string
    coop_answer?: string
  }
}

export const useSmartChat = () => {
  const { sendChatMessage } = useChat()
  const { searchSpeckleProjects, getProjectModels } = useSpeckle()

  /**
   * Determine if query is BIM/model related (should use Speckle) or document related (should use RAG)
   */
  function determineQueryIntent(message: string): ChatSource {
    const lowerMessage = message.toLowerCase()
    
    // BIM/Model-related keywords
    const bimKeywords = [
      'model', 'bim', '3d', 'speckle', 'structural', 'element', 'beam', 'column',
      'foundation', 'truss', 'frame', 'viewer', 'geometry', 'ifc', 'project id',
      'load', 'analysis', 'design', 'structural element'
    ]
    
    // Document/PDF related keywords
    const docKeywords = [
      'document', 'pdf', 'drawing', 'specification', 'code', 'standard', 'reference',
      'manual', 'page', 'section', 'chapter', 'report', 'file', 'spec'
    ]
    
    const hasBimKeywords = bimKeywords.some(keyword => lowerMessage.includes(keyword))
    const hasDocKeywords = docKeywords.some(keyword => lowerMessage.includes(keyword))
    
    // If both, use hybrid (both systems)
    if (hasBimKeywords && hasDocKeywords) {
      return 'hybrid'
    }
    
    // If BIM keywords present, use Speckle
    if (hasBimKeywords) {
      return 'speckle'
    }
    
    // Default to RAG for document queries
    return 'rag'
  }

  /**
   * Send message to appropriate backend based on intent
   */
  async function sendSmartMessage(
    message: string,
    context?: {
      currentProjectId?: string
      currentTask?: string
      sessionId?: string
      dataSources?: {
        project_db?: boolean
        code_db?: boolean
        coop_manual?: boolean
      }
    }
  ): Promise<SmartChatResponse> {
    const intent = determineQueryIntent(message)
    const sessionId = context?.sessionId || 'default'
    
    // For BIM queries, try Speckle GraphQL first, then fallback to RAG if needed
    if (intent === 'speckle' || intent === 'hybrid') {
      try {
        // Try Speckle GraphQL queries for BIM data
        // For now, we'll route through RAG backend which can handle BIM queries
        // In the future, you might want direct GraphQL calls here
        const ragResponse = await sendChatMessage(message, sessionId, undefined, context?.dataSources)
        
        // Handle multi-answer responses (matching web-app behavior)
        const hasProjectAnswer = ragResponse.project_answer && ragResponse.project_answer.trim()
        const hasCodeAnswer = ragResponse.code_answer && ragResponse.code_answer.trim()
        const hasCoopAnswer = ragResponse.coop_answer && ragResponse.coop_answer.trim()
        
        let combinedMessage = ''
        if (hasProjectAnswer || hasCodeAnswer || hasCoopAnswer) {
          const parts: string[] = []
          if (hasProjectAnswer) {
            parts.push(ragResponse.project_answer!)
          }
          if (hasCodeAnswer) {
            parts.push(`## Code References\n\n${ragResponse.code_answer}`)
          }
          if (hasCoopAnswer) {
            parts.push(`## Training Manual References\n\n${ragResponse.coop_answer}`)
          }
          combinedMessage = parts.join('\n\n---\n\n')
        } else {
          combinedMessage = ragResponse.reply || 'No response'
        }
        
        return {
          message: combinedMessage,
          source: intent === 'hybrid' ? 'hybrid' : 'speckle',
          metadata: {
            projectId: ragResponse.model_info?.projectId,
            modelId: ragResponse.model_info?.modelId,
            citations: ragResponse.citations,
            route: ragResponse.route,
            project_answer: ragResponse.project_answer,
            code_answer: ragResponse.code_answer,
            coop_answer: ragResponse.coop_answer,
          }
        }
      } catch (error) {
        console.error('Speckle query failed, falling back to RAG:', error)
        // Fallback to RAG
        const ragResponse = await sendChatMessage(message, sessionId, undefined, context?.dataSources)
        
        // Handle multi-answer responses (matching web-app behavior)
        const hasProjectAnswer = ragResponse.project_answer && ragResponse.project_answer.trim()
        const hasCodeAnswer = ragResponse.code_answer && ragResponse.code_answer.trim()
        const hasCoopAnswer = ragResponse.coop_answer && ragResponse.coop_answer.trim()
        
        let combinedMessage = ''
        if (hasProjectAnswer || hasCodeAnswer || hasCoopAnswer) {
          const parts: string[] = []
          if (hasProjectAnswer) {
            parts.push(ragResponse.project_answer!)
          }
          if (hasCodeAnswer) {
            parts.push(`## Code References\n\n${ragResponse.code_answer}`)
          }
          if (hasCoopAnswer) {
            parts.push(`## Training Manual References\n\n${ragResponse.coop_answer}`)
          }
          combinedMessage = parts.join('\n\n---\n\n')
        } else {
          combinedMessage = ragResponse.reply || 'No response'
        }
        
        return {
          message: combinedMessage,
          source: 'rag',
          metadata: {
            citations: ragResponse.citations,
            route: ragResponse.route,
            project_answer: ragResponse.project_answer,
            code_answer: ragResponse.code_answer,
            coop_answer: ragResponse.coop_answer,
          }
        }
      }
    }
    
    // For document queries, use RAG backend
    const ragResponse = await sendChatMessage(message, sessionId, undefined, context?.dataSources)
    
    // Handle multi-answer responses (matching web-app behavior)
    // The backend may return separate answers for each database
    const hasProjectAnswer = ragResponse.project_answer && ragResponse.project_answer.trim()
    const hasCodeAnswer = ragResponse.code_answer && ragResponse.code_answer.trim()
    const hasCoopAnswer = ragResponse.coop_answer && ragResponse.coop_answer.trim()
    
    // Combine answers if multiple exist, otherwise use reply or first available
    let combinedMessage = ''
    if (hasProjectAnswer || hasCodeAnswer || hasCoopAnswer) {
      const parts: string[] = []
      if (hasProjectAnswer) {
        parts.push(ragResponse.project_answer!)
      }
      if (hasCodeAnswer) {
        parts.push(`## Code References\n\n${ragResponse.code_answer}`)
      }
      if (hasCoopAnswer) {
        parts.push(`## Training Manual References\n\n${ragResponse.coop_answer}`)
      }
      combinedMessage = parts.join('\n\n---\n\n')
    } else {
      // Fallback to reply, answer, or 'No response'
      combinedMessage = ragResponse.reply || 'No response'
    }
    
    return {
      message: combinedMessage,
      source: 'rag',
      metadata: {
        citations: ragResponse.citations,
        route: ragResponse.route,
        project_answer: ragResponse.project_answer,
        code_answer: ragResponse.code_answer,
        coop_answer: ragResponse.coop_answer,
      }
    }
  }

  return {
    sendSmartMessage,
    determineQueryIntent,
    searchSpeckleProjects,
    getProjectModels
  }
}

