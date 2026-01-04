interface ChatResponse {
  reply: string  // Backend uses 'reply' not 'answer'
  message?: string  // Alternative field name
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
  // Agent thinking log (for Agent Thinking panel)
  thinking_log?: string[]
}

interface StreamCallbacks {
  onLog?: (log: { type: string; message: string; timestamp: number; node?: string }) => void
  onChunk?: (chunk: string) => void
  onComplete?: (result: ChatResponse) => void
  onError?: (error: Error) => void
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

  async function sendChatMessageStream(
    message: string,
    sessionId: string = 'default',
    images?: string[],
    dataSources?: {
      project_db?: boolean
      code_db?: boolean
      coop_manual?: boolean
    },
    callbacks?: StreamCallbacks
  ): Promise<void> {
    const url = `${config.public.orchestratorUrl}/chat/stream`
    console.log('📤 Starting streaming chat to:', url)
    console.log('📝 Message:', message)
    console.log('📚 Data Sources:', dataSources || 'all enabled')
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          images_base64: images,
          data_sources: dataSources || {
            project_db: true,
            code_db: true,
            coop_manual: true
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body reader available')
      }
      
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('✅ Stream completed')
          break
        }
        
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'connected') {
                console.log('✅ SSE stream connected:', data.message_id)
              } else if (data.type === 'thinking') {
                // Emit thinking log
                console.log('💭 Thinking:', data.message?.substring(0, 100) + '...')
                callbacks?.onLog?.({
                  type: 'thinking',
                  message: data.message,
                  node: data.node,
                  timestamp: data.timestamp
                })
              } else if (data.type === 'complete') {
                // Final result
                console.log('✅ Stream complete, got result')
                callbacks?.onComplete?.(data.result as ChatResponse)
              } else if (data.type === 'error') {
                console.error('❌ Stream error:', data.message)
                callbacks?.onError?.(new Error(data.message || 'Unknown error'))
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, line)
            }
          }
        }
      }
    } catch (error: any) {
      console.error('❌ SSE stream error:', error)
      callbacks?.onError?.(error)
      throw error
    }
  }

  return {
    sendChatMessage,
    sendChatMessageStream
  }
}


