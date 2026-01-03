<template>
  <div
    v-if="isOpen"
    class="absolute bottom-0 left-0 right-0 border-t border-gray-200 shadow-2xl"
    :style="{ 
      height: `${panelHeight}px`, 
      maxHeight: '70vh', 
      minHeight: '200px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      width: '100%',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(20px)',
      zIndex: 50
    }"
  >
    <!-- Resize Handle (top edge) -->
    <div
      class="absolute top-0 left-0 right-0 h-1 bg-gray-200 cursor-ns-resize hover:bg-purple-400 transition-colors"
      @mousedown="(e) => $emit('resize-start', e, panelHeight)"
    ></div>

    <!-- Logs Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h3 class="font-semibold text-gray-900 text-base" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">Agent Thinking</h3>
          <p class="text-xs text-gray-500 mt-0.5" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">Real-time reasoning and decision process</p>
        </div>
        <span v-if="logs.length > 0" class="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full border border-purple-200">
          {{ logs.length }} {{ logs.length === 1 ? 'thought' : 'thoughts' }}
        </span>
      </div>
      <button
        @click="$emit('close')"
        class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-gray-900"
        title="Close Logs"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Logs Content -->
    <div class="overflow-y-auto p-6 space-y-4 flex-1 bg-white/50 backdrop-blur-sm" style="min-height: 0;">
      <div v-if="logs.length === 0" class="text-center py-12">
        <div class="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center bg-gray-100">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <p class="text-gray-500" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">Agent thinking will appear here as you interact with the system.</p>
      </div>

      <div
        v-for="log in logs"
        :key="log.id"
        class="rounded-2xl p-6 transition-all duration-200 border-l-4 log-entry bg-white shadow-sm hover:shadow-md"
        :class="getLogBorderColor(log.type)"
      >
        <div class="flex items-center gap-3 mb-4">
          <span class="text-xs text-gray-500 font-mono" style="font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;">{{ formatTime(log.timestamp) }}</span>
        </div>

        <!-- Render markdown/rich text content -->
        <div 
          class="text-gray-800 prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-purple-600 prose-code:bg-purple-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200 prose-ul:text-gray-700 prose-ol:text-gray-700 prose-li:text-gray-700"
          style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; background-color: transparent;"
          v-html="formatThinking(log.thinking)"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface AgentLog {
  id: string
  type: 'thinking' | 'action' | 'result' | 'error'
  thinking: string  // Markdown/rich text content
  timestamp: Date
}

const props = withDefaults(defineProps<{
  isOpen: boolean
  logs: AgentLog[]
  panelHeight?: number
}>(), {
  panelHeight: 384
})

defineEmits<{
  open: []
  close: []
  'resize-start': [e: MouseEvent, currentHeight: number]
}>()

function getLogBorderColor(type: AgentLog['type']): string {
  const colors = {
    thinking: 'border-purple-400',
    action: 'border-purple-400',
    result: 'border-green-400',
    error: 'border-red-400'
  }
  return colors[type] || 'border-gray-300'
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  })
}

// Simple markdown-like formatting (can be enhanced with a proper markdown parser later)
function formatThinking(text: string): string {
  if (!text) return ''
  
  // Convert markdown-style formatting to HTML
  let html = text
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-900 mt-4 mb-2">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-900 mt-5 mb-3">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-semibold text-gray-900 mt-6 mb-4">$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    // Bullet points
    .replace(/^[-*] (.*$)/gim, '<li class="ml-4 mb-1 text-gray-700">$1</li>')
    // Numbered lists
    .replace(/^\d+\. (.*$)/gim, '<li class="ml-4 mb-1 text-gray-700">$1</li>')
    // Line breaks
    .replace(/\n\n/g, '</p><p class="mb-3 leading-relaxed text-gray-700">')
    .replace(/\n/g, '<br>')
  
  // Wrap lists
  html = html.replace(/(<li.*<\/li>)/gs, '<ul class="list-disc list-inside space-y-1 my-3 ml-4">$1</ul>')
  
  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<')) {
    html = '<p class="mb-3 leading-relaxed text-gray-700">' + html + '</p>'
  } else if (!html.includes('<p')) {
    html = '<p class="mb-3 leading-relaxed text-gray-700">' + html + '</p>'
  }
  
  return html
}
</script>

<style scoped>
.log-entry:hover {
  background-color: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}
</style>
