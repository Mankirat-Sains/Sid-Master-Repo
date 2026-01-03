interface ChatResponse {
  reply: string  // Backend uses 'reply' not 'answer'
  citations?: number
  route?: string
  project_answer?: string
  code_answer?: string
  coop_answer?: string
  project_citations?: number
  code_citations?: number
  coop_citations?: number
  image_similarity_results?: Array<Record<string, unknown>>
  message_id?: string
  latency_ms?: number
  timestamp?: string
  session_id?: string
  // Model information that orchestrator can return
  model_info?: {
    projectId: string
    modelId: string
    commitId?: string
    projectNumber?: string
  }
}

export const useChat = () => {
  const config = useRuntimeConfig()

  async function sendChatMessage(
    message: string,
    sessionId: string = 'default',
    images?: string[],
    dataSources?: {
      project_db?: boolean
      code_db?: boolean
      coop_manual?: boolean
    }
  ): Promise<ChatResponse> {
    const url = `${config.public.orchestratorUrl}/chat`
    console.log('📤 Sending chat message to:', url)
    console.log('📝 Message:', message)
    console.log('📚 Data Sources:', dataSources || 'all enabled')
    
    try {
      const response = await $fetch<ChatResponse>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          message,
          session_id: sessionId,
          images_base64: images,
          // Use provided data sources or default to all enabled
          data_sources: dataSources || {
            project_db: true,
            code_db: true,
            coop_manual: true
          }
        }
      })
      
      console.log('✅ Chat response received:', response)
      
      // Check if response contains an error message
      if (response.reply && response.reply.toLowerCase().includes('error')) {
        console.warn('⚠️ Backend returned error in response:', response.reply)
      }
      
      return response
    } catch (error: any) {
      console.error('❌ Chat API error:', error)
      console.error('❌ Error details:', {
        message: error.message,
        status: error.status,
        statusText: error.statusText,
        data: error.data
      })
      
      // Re-throw with more context
      const errorMessage = error.data?.detail || error.message || 'Unknown error'
      throw new Error(`Backend error: ${errorMessage}`)
    }
  }

  return {
    sendChatMessage
  }
}

