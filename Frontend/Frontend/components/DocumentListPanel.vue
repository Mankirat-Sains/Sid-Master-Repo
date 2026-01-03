<template>
  <div
    v-if="isOpen"
    class="absolute left-0 top-0 bottom-0 bg-white/95 backdrop-blur-sm border-r border-gray-200 shadow-2xl z-30 transition-all overflow-hidden"
    :style="{ width: `${width}px`, minWidth: '320px', maxWidth: '40%' }"
  >
    <!-- Header -->
    <div class="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="font-semibold text-lg text-gray-900" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ title || 'Documents' }}</h3>
        <p v-if="subtitle" class="text-xs text-gray-500 mt-1" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ subtitle }}</p>
      </div>
      <button
        @click="$emit('close')"
        class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-gray-900"
        title="Close"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Resize Handle -->
    <div
      class="absolute right-0 top-0 bottom-0 w-1 bg-gray-200 cursor-ew-resize hover:bg-purple-400 transition-colors"
      @mousedown="handleResizeStart"
    ></div>

    <!-- Document List -->
    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="documents.length === 0" class="text-center py-12">
        <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-400 font-medium" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">No documents found</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="(doc, index) in documents"
          :key="doc.id || index"
          @click="selectDocument(doc)"
          :class="[
            'p-4 rounded-xl border-2 cursor-pointer transition-all backdrop-blur-sm',
            selectedDocumentId === doc.id
              ? 'border-purple-400 bg-purple-50/80 shadow-lg'
              : 'border-gray-200 bg-white/60 hover:border-purple-300 hover:bg-white/80 hover:shadow-md'
          ]"
        >
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-purple-100 to-purple-200 rounded-xl flex items-center justify-center shadow-sm">
              <!-- Show 3D/cube icon for Speckle models, document icon for PDFs -->
              <svg v-if="doc.metadata?.projectId && doc.metadata?.modelId" class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <svg v-else class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="font-semibold text-gray-900 mb-1 truncate" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ doc.title || doc.name || 'Untitled Document' }}</h4>
              <p v-if="doc.description" class="text-sm text-gray-600 mb-2 line-clamp-2" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ doc.description }}</p>
              <div v-if="doc.metadata" class="flex flex-wrap gap-2">
                <span
                  v-for="(value, key) in doc.metadata"
                  :key="key"
                  class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded"
                  style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                >
                  {{ key }}: {{ value }}
                </span>
              </div>
              <div v-if="doc.reason" class="mt-2 p-2 bg-purple-50/80 backdrop-blur-sm border border-purple-200 rounded-lg text-xs text-purple-800" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">
                <span class="font-semibold">Why selected:</span> {{ doc.reason }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Document {
  id: string
  title?: string
  name?: string
  description?: string
  url?: string
  filePath?: string
  metadata?: Record<string, string | number | undefined>
  reason?: string
}

interface Props {
  isOpen: boolean
  title?: string
  subtitle?: string
  documents: Document[]
  width?: number
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  title: 'Documents',
  documents: () => [],
  width: 400
})

const emit = defineEmits<{
  close: []
  'select-document': [document: Document]
  'resize': [width: number]
}>()

const selectedDocumentId = ref<string | null>(null)
const resizing = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(400)

function selectDocument(doc: Document) {
  selectedDocumentId.value = doc.id
  emit('select-document', doc)
}

function handleResizeStart(e: MouseEvent) {
  resizing.value = true
  resizeStartX.value = e.clientX
  resizeStartWidth.value = props.width
  e.preventDefault()
  
  const handleMouseMove = (e: MouseEvent) => {
    if (!resizing.value) return
    const delta = resizeStartX.value - e.clientX
    const newWidth = Math.max(320, Math.min(window.innerWidth * 0.4, resizeStartWidth.value + delta))
    emit('resize', newWidth)
  }
  
  const handleMouseUp = () => {
    resizing.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}
</script>

