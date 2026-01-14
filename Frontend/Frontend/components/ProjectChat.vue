<template>
  <div class="h-full flex flex-col bg-[#0f0f0f] text-white">
    <!-- Header -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-white/10 bg-[#111]">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-semibold text-white">Chat</h3>
          <p class="text-xs text-white/50">Scoped to: {{ projectId }}</p>
        </div>
        <div v-if="openFiles.length > 0" class="flex items-center gap-2">
          <span class="text-xs text-white/40">{{ openFiles.length }} file(s) open</span>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center space-y-4">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <div class="max-w-md">
          <h4 class="text-lg font-semibold text-white mb-2">Project Assistant</h4>
          <p class="text-white/60 text-sm">
            Ask questions about the files in this project. I'll prioritize information from this folder, but can also search across all projects when needed.
          </p>
        </div>
      </div>

      <!-- Message List -->
      <div v-for="message in messages" :key="message.id" class="flex gap-3">
        <!-- Avatar -->
        <div 
          class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center"
          :class="message.role === 'user' ? 'bg-blue-600' : 'bg-gradient-to-br from-purple-500 to-purple-700'"
        >
          <svg v-if="message.role === 'user'" class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <svg v-else class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        
        <!-- Message Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-medium text-white">{{ message.role === 'user' ? 'You' : 'Sid' }}</span>
            <span class="text-xs text-white/40">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="prose prose-invert prose-sm max-w-none text-white/80" v-html="formatContent(message.content)"></div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex gap-3">
        <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-purple-500 to-purple-700">
          <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-medium text-white">Sid</span>
          </div>
          <div class="flex items-center gap-2 text-white/60">
            <div class="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 0ms"></div>
            <div class="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 150ms"></div>
            <div class="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 300ms"></div>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChat } from '~/composables/useChat'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface OpenFile {
  id: string
  name: string
  path: string
  type: string
}

const props = defineProps<{
  projectId: string
  folderPath: string
  openFiles: OpenFile[]
}>()

const { sendChatMessage } = useChat()

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
    
    const response = await sendChatMessage(contextMessage, sessionId)
    
    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: response.reply || 'No response',
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
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

function formatContent(content: string): string {
  // Basic markdown-like formatting
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-white/10 px-1 rounded">$1</code>')
    .replace(/\n/g, '<br>')
}

watch(messages, () => {
  nextTick(scrollToBottom)
}, { deep: true })
</script>
