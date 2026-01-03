<template>
  <div class="h-full w-full flex flex-col bg-white">
    <!-- PDF Viewer Header -->
    <div class="flex-shrink-0 bg-slate-800 text-white px-6 py-3 flex items-center justify-between border-b border-slate-700">
      <div class="flex items-center gap-3">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3 class="font-semibold">{{ fileName || 'PDF Document' }}</h3>
      </div>
      <div class="flex items-center gap-2">
        <!-- Zoom Controls -->
        <button
          @click="zoomOut"
          class="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          title="Zoom Out"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
          </svg>
        </button>
        <span class="text-sm px-2">{{ Math.round(zoom * 100) }}%</span>
        <button
          @click="zoomIn"
          class="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          title="Zoom In"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
          </svg>
        </button>
        <div class="w-px h-6 bg-slate-600"></div>
        <!-- Page Navigation -->
        <button
          @click="previousPage"
          :disabled="currentPage <= 1"
          class="p-2 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Previous Page"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span class="text-sm px-3">Page {{ currentPage }} of {{ totalPages || '?' }}</span>
        <button
          @click="nextPage"
          :disabled="currentPage >= (totalPages || 1)"
          class="p-2 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Next Page"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <div class="w-px h-6 bg-slate-600"></div>
        <!-- Close Button -->
        <button
          @click="$emit('close')"
          class="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          title="Close"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- PDF Content Area -->
    <div class="flex-1 overflow-auto bg-slate-100 p-4" @scroll="handleScroll">
      <div class="flex flex-col items-center gap-4" :style="{ transform: `scale(${zoom})`, transformOrigin: 'top center' }">
        <!-- Loading State -->
        <div v-if="loading" class="flex flex-col items-center justify-center py-20">
          <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p class="text-slate-600 font-medium">Loading PDF...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
          <svg class="w-16 h-16 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-red-600 font-medium mb-2">Error loading PDF</p>
          <p class="text-slate-500 text-sm">{{ error }}</p>
        </div>

        <!-- PDF Pages -->
        <div v-else-if="actualPdfUrl" class="w-full flex flex-col">
          <iframe
            :src="actualPdfUrl"
            class="w-full border border-slate-300 shadow-lg bg-white flex-1"
            style="min-height: 800px;"
            @load="handlePDFLoad"
            frameborder="0"
          ></iframe>
          
          <!-- Fallback download link -->
          <div class="mt-2 text-center bg-slate-50 p-2 rounded">
            <a 
              :href="actualPdfUrl" 
              target="_blank" 
              class="text-purple-600 hover:text-purple-700 underline text-sm"
            >
              PDF not displaying? Click to open in new tab
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface Props {
  fileUrl?: string
  fileName?: string
  pdfUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  fileUrl: '',
  fileName: '',
  pdfUrl: ''
})

const emit = defineEmits<{
  close: []
  loaded: []
  error: [error: string]
}>()

const loading = ref(true)
const error = ref<string | null>(null)
const currentPage = ref(1)
const totalPages = ref<number | null>(null)
const zoom = ref(1)

// Compute the actual PDF URL to use
const actualPdfUrl = computed(() => {
  let url = props.pdfUrl || props.fileUrl || ''
  
  if (!url) return ''
  
  // If it's already a full URL (http/https), use as-is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // If it's a relative path starting with /, construct full URL using current origin
  if (url.startsWith('/')) {
    // Use current window location to get the base URL
    // Encode the path properly to handle spaces and special characters in filenames
    if (typeof window !== 'undefined') {
      // Split the path into directory parts and encode each segment separately
      // This preserves slashes while encoding spaces and special chars in filenames
      const pathParts = url.split('/').filter(p => p) // Remove empty strings
      const encodedParts = pathParts.map(part => encodeURIComponent(part))
      const encodedPath = '/' + encodedParts.join('/')
      return `${window.location.origin}${encodedPath}`
    }
    // Fallback for SSR
    return url
  }
  
  return url
})

watch(() => actualPdfUrl.value, (newUrl) => {
  if (newUrl) {
    console.log('PDF URL changed:', newUrl)
    loadPDF()
  } else {
    loading.value = false
  }
}, { immediate: true })

function loadPDF() {
  loading.value = true
  error.value = null
  // Hide loading spinner after 2 seconds - PDFs often load but iframe load event doesn't fire reliably
  setTimeout(() => {
    loading.value = false
  }, 2000)
}

function handlePDFLoad(event?: Event) {
  console.log('✅ PDF loaded successfully:', actualPdfUrl.value, event)
  loading.value = false
  error.value = null
  emit('loaded')
}


function handlePDFError(event?: Event) {
  console.error('PDF load error:', event)
  loading.value = false
  error.value = 'Failed to load PDF. Please check the file path and ensure the file exists.'
  emit('error', error.value)
}

function zoomIn() {
  zoom.value = Math.min(zoom.value + 0.25, 3)
}

function zoomOut() {
  zoom.value = Math.max(zoom.value - 0.25, 0.5)
}

function previousPage() {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function nextPage() {
  if (totalPages.value && currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

function handleScroll() {
  // Could implement page detection based on scroll position
}
</script>

