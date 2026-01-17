<template>
  <div class="h-full flex flex-col bg-[#0f0f0f] text-white">
    <!-- Chat Header -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-white/10 bg-[#111]">
      <h3 class="text-lg font-semibold text-white">Chat (Test Server)</h3>
      <p class="text-xs text-white/60">Scoped to: {{ projectName }}</p>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start'
        ]"
      >
        <div
          :class="[
            'max-w-[80%] rounded-lg px-4 py-2',
            message.role === 'user'
              ? 'bg-purple-600 text-white'
              : 'bg-white/10 text-white'
          ]"
        >
          <p class="text-sm whitespace-pre-wrap">{{ message.content }}</p>
          <p class="text-xs opacity-60 mt-1">{{ formatTime(message.timestamp) }}</p>
        </div>
      </div>
      
      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-white/10 rounded-lg px-4 py-2">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
            <span class="text-sm text-white/60">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="flex-shrink-0 px-4 py-3 border-t border-white/10 bg-[#111]">
      <div class="flex gap-3">
        <div class="flex-1 relative">
          <textarea
            ref="inputRef"
            v-model="inputMessage"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.prevent="inputMessage += '\n'"
            placeholder="Ask about files in this project..."
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/40 resize-none focus:outline-none focus:border-purple-500/50 transition"
            rows="1"
          ></textarea>
        </div>
        <button
          @click="sendMessage"
          :disabled="!inputMessage.trim() || isLoading"
          class="w-10 h-10 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white flex items-center justify-center transition"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <p class="text-xs text-white/30 mt-2">Press Enter to send, Shift+Enter for new line</p>
      <p class="text-xs text-yellow-400/60 mt-1">⚠️ Using Test Server (port 8002)</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const props = defineProps<{
  projectId: string
  projectName: string
  folderPath: string
  openFiles: Array<{ id: string; name: string; path: string; type: string }>
}>()

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// Generate a session ID based on project
const sessionId = `project-${props.projectId}`

async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage: Message = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  const question = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true
  
  await nextTick()
  scrollToBottom()
  
  try {
    // Include folder context in the message
    const contextMessage = `[Context: User is working in project folder: ${props.folderPath}. Open files: ${props.openFiles.map(f => f.name).join(', ') || 'none'}]\n\n${question}`
    
    // Call test server directly
    const response = await fetch('http://localhost:8002/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: contextMessage,
        session_id: sessionId
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: result.reply || 'No response',
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
  } catch (error: any) {
    console.error('Chat error:', error)
    messages.value.push({
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: `Sorry, I encountered an error: ${error.message || 'Unknown error'}. Make sure the test server is running on port 8002.`,
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>
