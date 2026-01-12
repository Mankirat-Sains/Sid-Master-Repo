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
  workflow?: string
  task_type?: string
  doc_type?: string
  section_type?: string
  execution_trace?: Record<string, unknown>
  doc_generation_result?: Record<string, unknown>
  document_state?: Record<string, unknown>
  document_patch?: Record<string, unknown>
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
  onToken?: (token: { content: string; node: string; timestamp: number }) => void
  onChunk?: (chunk: string) => void
  onWorkflow?: (workflow: string) => void
  onDocument?: (payload: Record<string, unknown>) => void
  onComplete?: (result: ChatResponse) => void
  onError?: (error: Error) => void
  onInterrupt?: (interrupt: {
    interrupt_id: string | null
    interrupt_type: string
    question: string
    codes: string[]
    code_count: number
    chunk_count: number
    available_codes: string[]
    previously_retrieved: string[]
    session_id: string
    thread_id: string
  }) => void
}

interface StreamOptions {
  documentContext?: Record<string, unknown> | null
  workflowHint?: string
  selection?: Record<string, unknown> | null
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
    } | undefined,  // Keep for backwards compatibility but don't use
    options?: StreamOptions
  ): Promise<ChatResponse> {
    const url = `${config.public.orchestratorUrl}/chat`
    console.log('📤 Sending chat message to:', url)
    console.log('📝 Message:', message)
    console.log('📸 [useChat] images parameter received:', images)
    console.log('📸 [useChat] images length:', images?.length || 0)
    console.log('📸 [useChat] images first item preview:', images?.[0]?.substring(0, 50) || 'none')
    
    try {
      const requestBody: any = {
        message,
        session_id: sessionId,
        images_base64: images,
        workflow: options?.workflowHint,
        document_context: options?.documentContext || undefined,
        document_cursor: options?.selection || undefined
        // data_sources removed - backend router now intelligently selects databases automatically
      }
      
      console.log('📸 [useChat] Request body images_base64:', requestBody.images_base64 ? `${requestBody.images_base64.length} images` : 'undefined')
      console.log('📸 [useChat] Full request body keys:', Object.keys(requestBody))
      
      const response = await $fetch<ChatResponse>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: requestBody
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
    callbacks?: StreamCallbacks,
    options?: StreamOptions
  ): Promise<void> {
    const url = `${config.public.orchestratorUrl}/chat/stream`
    console.log('📤 Starting streaming chat to:', url)
    console.log('📝 Message:', message)
    console.log('📋 Callbacks provided:', {
      hasCallbacks: !!callbacks,
      hasOnLog: !!callbacks?.onLog,
      hasOnComplete: !!callbacks?.onComplete,
      hasOnError: !!callbacks?.onError
    })
    // dataSources removed - backend router now intelligently selects databases automatically
    
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
          workflow: options?.workflowHint,
          document_context: options?.documentContext || undefined,
          document_cursor: options?.selection || undefined
          // data_sources removed - backend router now intelligently selects databases automatically
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
              const workflowSignal = data.workflow || data.task_type || data.node
              const documentPayload = data.doc_generation_result || data.document_state || data.document_patch || data.document

              if (workflowSignal && callbacks?.onWorkflow) {
                callbacks.onWorkflow(workflowSignal)
              }
              if (documentPayload && callbacks?.onDocument) {
                callbacks.onDocument(documentPayload)
              }
              
              if (data.type === 'connected') {
                console.log('✅ SSE stream connected:', data.message_id)
              } else if (data.type === 'thinking') {
                // Emit thinking log
                console.log('💭 Thinking log received from stream:', {
                  node: data.node,
                  messageLength: data.message?.length,
                  messagePreview: data.message?.substring(0, 100) + '...',
                  hasCallbacks: !!callbacks,
                  hasOnLog: !!callbacks?.onLog
                })
                if (callbacks?.onLog) {
                  callbacks.onLog({
                    type: 'thinking',
                    message: data.message,
                    node: data.node,
                    timestamp: data.timestamp
                  })
                } else {
                  console.warn('⚠️ No onLog callback provided - thinking logs will not be displayed')
                }
              } else if (data.type === 'token') {
                // Real-time token streaming from LLM
                if (callbacks?.onToken) {
                  callbacks.onToken({
                    content: data.content,
                    node: data.node,
                    timestamp: data.timestamp
                  })
                }
              } else if (data.type === 'complete') {
                // Final result
                console.log('✅ Stream complete, got result')
                if (callbacks?.onWorkflow && (data.result?.workflow || data.result?.task_type)) {
                  callbacks.onWorkflow(data.result.workflow || data.result.task_type)
                }
                if (callbacks?.onDocument && (data.result?.doc_generation_result || data.result?.document_state || data.result?.document_patch)) {
                  callbacks.onDocument(data.result.doc_generation_result || data.result.document_state || data.result.document_patch)
                }
                callbacks?.onComplete?.(data.result as ChatResponse)
              } else if (data.type === 'interrupt') {
                // Human-in-the-loop interrupt - requires user input
                console.log('⏸️  Interrupt received from stream:', {
                  interrupt_type: data.interrupt_type,
                  codes: data.codes?.length || 0,
                  available_codes: data.available_codes?.length || 0,
                  question: data.question
                })
                if (callbacks?.onInterrupt) {
                  callbacks.onInterrupt({
                    interrupt_id: data.interrupt_id,
                    interrupt_type: data.interrupt_type,
                    question: data.question || '',
                    codes: data.codes || [],
                    code_count: data.code_count || 0,
                    chunk_count: data.chunk_count || 0,
                    available_codes: data.available_codes || [],
                    previously_retrieved: data.previously_retrieved || [],
                    session_id: data.session_id || sessionId,
                    thread_id: data.thread_id || sessionId
                  })
                } else {
                  console.warn('⚠️ No onInterrupt callback provided - interrupt will not be handled')
                }
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
