<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="border-b border-foundation-line bg-foundation-2 p-4">
      <div>
        <h2 class="text-xl font-semibold">Document Intelligence</h2>
        <p class="text-sm text-foreground-muted">
          Ask questions about PDFs, technical drawings, and engineering documents
        </p>
      </div>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div
        v-for="message in messages"
        :key="message.id"
        class="flex flex-col"
        :class="message.role === 'user' ? 'items-end' : 'items-start'"
      >
        <div
          class="max-w-[85%] rounded-lg p-3"
          :class="
            message.role === 'user'
              ? 'bg-primary text-primary-content'
              : 'bg-foundation-2 text-foreground'
          "
        >
          <div class="whitespace-pre-wrap" v-html="message.content"></div>
          <p v-if="message.timestamp" class="text-xs mt-1 opacity-70">
            {{ formatTime(message.timestamp) }}
          </p>
          <!-- Citations -->
          <div
            v-if="message.citations && message.citations.length > 0"
            class="mt-2 pt-2 border-t border-current/20"
          >
            <p class="text-xs font-semibold mb-1">Sources:</p>
            <div class="space-y-1">
              <div
                v-for="(citation, idx) in message.citations"
                :key="idx"
                class="text-xs"
              >
                {{ citation }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="isLoading"
        class="flex items-center gap-2 text-foreground-muted"
      >
        <div
          class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
        <span>Analyzing documents...</span>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-foundation-line bg-foundation-2 p-4">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="Ask about documents, drawings, or technical specifications..."
          class="flex-1 px-4 py-2 rounded-lg border border-foundation-line bg-foundation text-foreground placeholder-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary"
          :disabled="isLoading"
        />
        <button
          type="submit"
          :disabled="!inputMessage.trim() || isLoading"
          class="px-6 py-2 rounded-lg bg-primary text-primary-content hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: string[]
}

const { sendChatMessage } = useChat()

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date(),
  }

  messages.value.push(userMessage)
  const question = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true

  // Scroll to bottom
  await nextTick()
  scrollToBottom()

  try {
    // Send to RAG backend
    const response = await sendChatMessage(question, 'document-chat')

    // Extract answer and citations
    const answerText = response.reply || response.answer || 'No response'
    const citations: string[] = []

    // Extract citations if available
    if (response.citations) {
      citations.push(`${response.citations} source(s) referenced`)
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: answerText,
      timestamp: new Date(),
      citations: citations.length > 0 ? citations : undefined,
    }

    messages.value.push(assistantMessage)
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please check that the RAG backend is running and try again.',
      timestamp: new Date(),
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
</script>

