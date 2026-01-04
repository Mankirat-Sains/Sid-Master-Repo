<template>
  <div class="flex flex-col h-full">
    <!-- PDF Controls -->
    <div
      v-if="numPages > 0"
      class="flex items-center justify-between p-4 border-b border-outline-3"
    >
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="p-2 rounded hover:bg-foundation-3 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage <= 1"
          @click="previousPage"
        >
          <ChevronLeft class="size-4" />
        </button>
        <span class="text-body-sm">Page {{ currentPage }} of {{ numPages }}</span>
        <button
          type="button"
          class="p-2 rounded hover:bg-foundation-3 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage >= numPages"
          @click="nextPage"
        >
          <ChevronRight class="size-4" />
        </button>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="p-2 rounded hover:bg-foundation-3"
          @click="zoomOut"
        >
          <ZoomOut class="size-4" />
        </button>
        <span class="text-body-sm min-w-[60px] text-center">
          {{ Math.round(scale * 100) }}%
        </span>
        <button type="button" class="p-2 rounded hover:bg-foundation-3" @click="zoomIn">
          <ZoomIn class="size-4" />
        </button>
      </div>
    </div>

    <!-- PDF Canvas Container -->
    <div class="flex-1 overflow-auto bg-foundation-3 flex justify-center p-4">
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="size-8 animate-spin mx-auto mb-2 text-foreground-2" />
          <p class="text-body-sm text-foreground-2">Loading PDF...</p>
        </div>
      </div>
      <div v-else-if="error" class="flex items-center justify-center h-full">
        <div class="text-center">
          <TriangleAlert class="size-8 mx-auto mb-2 text-danger" />
          <p class="text-body-sm text-foreground-2">{{ error }}</p>
        </div>
      </div>
      <canvas
        v-else
        ref="canvasRef"
        class="shadow-lg max-w-full"
        :style="{ transform: `scale(${scale})`, transformOrigin: 'top center' }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, shallowRef, nextTick } from 'vue'
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Loader2,
  TriangleAlert
} from 'lucide-vue-next'

// Dynamically import PDF.js only on client side to avoid SSR issues
let pdfjsLib: typeof import('pdfjs-dist') | null = null
const isClient = typeof window !== 'undefined'

const props = defineProps<{
  url: string
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const numPages = ref(0)
const currentPage = ref(1)
const scale = ref(1.0)
// Use shallowRef for PDF document to avoid Vue reactivity issues with PDF.js objects
// PDF.js objects contain complex internal state that shouldn't be made reactive
const pdfDoc = shallowRef<any>(null)
const renderTask = shallowRef<any>(null)
const loadingTask = shallowRef<any>(null)
const isDestroyed = ref(false)

// Helper function to check if PDF document is valid
const isPdfDocValid = (doc: any): boolean => {
  if (!doc) return false
  // Check if document has required methods and properties
  return (
    typeof doc.getPage === 'function' &&
    typeof doc.numPages === 'number' &&
    typeof doc.destroy === 'function' &&
    doc.numPages > 0
  )
}

const loadPdf = async () => {
  if (!isClient) return

  try {
    loading.value = true
    error.value = null
    isDestroyed.value = false

    // Clean up previous document and render task
    if (renderTask.value) {
      try {
        renderTask.value.cancel()
      } catch {
        // Ignore cancellation errors
      }
      renderTask.value = null
    }

    if (pdfDoc.value) {
      try {
        pdfDoc.value.destroy()
      } catch {
        // Ignore destroy errors
      }
      pdfDoc.value = null
    }

    // Cancel any in-flight loading task
    if (loadingTask.value) {
      try {
        loadingTask.value.destroy()
      } catch {
        // Ignore cancellation errors
      }
      loadingTask.value = null
    }

    // Ensure PDF.js is loaded
    if (!pdfjsLib) {
      pdfjsLib = await import('pdfjs-dist')
      // Use local PDF.js worker file from public folder
      // This avoids CDN issues and works better with Supabase URLs
      // Set worker source before any PDF operations
      if (pdfjsLib.GlobalWorkerOptions) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
      }
    }

    // Verify PDF.js is properly initialized
    if (!pdfjsLib || !pdfjsLib.getDocument) {
      throw new Error('PDF.js library failed to load properly')
    }

    // Check if component was destroyed during async operation
    if (isDestroyed.value) return

    // Fetch PDF as ArrayBuffer to avoid CORS and redirect issues
    // This ensures PDF.js receives the data directly without URL-based issues
    let pdfData: ArrayBuffer

    // Normalize URL to use the same host as current origin to avoid cross-origin issues
    // Fixes issue where localhost:3000 vs 127.0.0.1:3000 are treated as different origins
    let fetchUrl = props.url
    try {
      // Check if URL is relative or absolute
      const isAbsolute =
        props.url.startsWith('http://') || props.url.startsWith('https://')

      if (isAbsolute) {
        const urlObj = new URL(props.url)
        const currentOrigin = window.location

        // If the URL host differs from current origin host (e.g., localhost vs 127.0.0.1)
        // but they're both localhost/127.0.0.1 and on the same port, use the current origin's host
        const isLocalhost =
          urlObj.hostname === 'localhost' || urlObj.hostname === '127.0.0.1'
        const isCurrentLocalhost =
          currentOrigin.hostname === 'localhost' ||
          currentOrigin.hostname === '127.0.0.1'

        if (
          isLocalhost &&
          isCurrentLocalhost &&
          urlObj.port === currentOrigin.port &&
          urlObj.protocol === currentOrigin.protocol &&
          urlObj.hostname !== currentOrigin.hostname
        ) {
          // Replace hostname with current origin's hostname to ensure same-origin
          urlObj.hostname = currentOrigin.hostname
          fetchUrl = urlObj.toString()
          console.log(`[PdfViewer] Normalized URL from ${props.url} to ${fetchUrl}`)
        }
      } else {
        // Relative URL - use as-is, it will automatically use current origin
        fetchUrl = new URL(props.url, window.location.href).toString()
      }
    } catch (urlError) {
      // If URL parsing fails, use original URL
      console.warn('[PdfViewer] Failed to normalize URL:', urlError)
    }

    // Check if this is an API endpoint that will redirect to Supabase
    const isApiRequest = fetchUrl.includes('/api/stream')
    const isSupabaseUrl = fetchUrl.includes('supabase.co/storage/v1/object/public')
    const urlObj = new URL(fetchUrl, window.location.href)
    const isSameOrigin = urlObj.origin === window.location.origin

    // For API endpoints, use PDF.js directly - it handles redirects automatically
    // Use withCredentials: false to avoid CORS issues with Supabase (it's public anyway)
    // The API endpoint should work without credentials since it just redirects
    if (isApiRequest) {
      console.log(
        '[PdfViewer] Loading PDF from API endpoint (PDF.js will handle redirect):',
        fetchUrl
      )
      const task = pdfjsLib.getDocument({
        url: fetchUrl,
        httpHeaders: {},
        withCredentials: false // Don't send credentials - avoids CORS issues with Supabase redirect
      })
      loadingTask.value = task
      const pdf = await task.promise

      if (isDestroyed.value) {
        try {
          pdf.destroy()
        } catch {
          // Ignore destroy errors
        }
        return
      }

      if (!isPdfDocValid(pdf)) {
        throw new Error('Loaded PDF document is invalid')
      }

      pdfDoc.value = pdf
      numPages.value = pdf.numPages
      loadingTask.value = null
      loading.value = false

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      let retries = 0
      while (!canvasRef.value && retries < 20 && !isDestroyed.value) {
        await new Promise((resolve) => setTimeout(resolve, 50))
        await nextTick()
        retries++
      }

      if (!isDestroyed.value && canvasRef.value) {
        await renderPage(1)
      } else if (!isDestroyed.value) {
        error.value = 'Failed to initialize PDF canvas'
        console.error('Canvas not available after waiting')
      }
      return
    }

    // For direct Supabase URLs or other URLs, fetch as ArrayBuffer
    try {
      if (isSupabaseUrl) {
        // Direct Supabase URL - no credentials needed (it's public, avoids CORS wildcard issue)
        const response = await fetch(fetchUrl, {
          mode: 'cors',
          credentials: 'omit' // Public URL, no credentials needed
        })

        if (!response.ok) {
          throw new Error(
            `Failed to fetch PDF: ${response.status} ${response.statusText}`
          )
        }

        pdfData = await response.arrayBuffer()
      } else {
        // Other URLs - use credentials for authenticated requests
        const response = await fetch(fetchUrl, {
          mode: isSameOrigin ? 'same-origin' : 'cors',
          credentials: isSameOrigin ? 'include' : 'same-origin'
        })

        if (!response.ok) {
          throw new Error(
            `Failed to fetch PDF: ${response.status} ${response.statusText}`
          )
        }

        pdfData = await response.arrayBuffer()
      }
    } catch (fetchError) {
      console.error('[PdfViewer] Error fetching PDF data:', fetchError)
      throw fetchError
    }

    // Load PDF from ArrayBuffer - this avoids URL-related issues
    // Using ArrayBuffer ensures PDF.js receives clean data without redirect/CORS complications
    const task = pdfjsLib.getDocument({
      data: pdfData
    })
    loadingTask.value = task

    const pdf = await task.promise

    // Check again if component was destroyed
    if (isDestroyed.value) {
      try {
        pdf.destroy()
      } catch {
        // Ignore destroy errors
      }
      return
    }

    // Verify the loaded PDF is valid before storing it
    if (!isPdfDocValid(pdf)) {
      throw new Error('Loaded PDF document is invalid')
    }

    pdfDoc.value = pdf
    numPages.value = pdf.numPages
    loadingTask.value = null

    // Clear loading state so canvas appears in DOM (canvas only renders when !loading && !error)
    loading.value = false

    // Wait for Vue to update the DOM and canvas to be available
    await nextTick()
    // Additional wait to ensure canvas is fully mounted
    await new Promise((resolve) => setTimeout(resolve, 100))

    // Wait for canvas ref to be available (retry if needed)
    let retries = 0
    while (!canvasRef.value && retries < 20 && !isDestroyed.value) {
      await new Promise((resolve) => setTimeout(resolve, 50))
      await nextTick()
      retries++
    }

    // Force initial render of page 1 - ensure it actually renders
    if (!isDestroyed.value && canvasRef.value) {
      await renderPage(1)
    } else if (!isDestroyed.value) {
      error.value = 'Failed to initialize PDF canvas'
      console.error('Canvas not available after waiting')
    }
  } catch (err) {
    // Don't set error if operation was cancelled
    if (isDestroyed.value) return

    error.value = err instanceof Error ? err.message : 'Failed to load PDF'
    console.error('PDF loading error:', err)
    loading.value = false // Ensure loading is cleared on error
  }
}

const renderPage = async (pageNum: number) => {
  // Validate document and canvas are available
  if (!canvasRef.value || isDestroyed.value) {
    // If canvas isn't ready yet, wait a bit and try again
    if (!canvasRef.value && !isDestroyed.value) {
      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))
      if (!canvasRef.value || isDestroyed.value) {
        console.warn('Canvas not available for rendering')
        return
      }
    } else {
      return
    }
  }

  // Validate page number
  if (pageNum < 1 || pageNum > numPages.value) {
    console.warn(`Invalid page number: ${pageNum} (total pages: ${numPages.value})`)
    return
  }

  // Validate PDF document is still valid before proceeding
  if (!isPdfDocValid(pdfDoc.value)) {
    error.value = 'PDF document is no longer valid. Please reload the PDF.'
    console.error('PDF document validation failed')
    return
  }

  // Store a reference to the document we're about to use
  const doc = pdfDoc.value
  if (!doc || isDestroyed.value) return

  try {
    // Cancel any existing render task
    if (renderTask.value) {
      try {
        renderTask.value.cancel()
      } catch {
        // Ignore cancellation errors
      }
      renderTask.value = null
    }

    // Double-check document is still valid before async operation
    if (!isPdfDocValid(pdfDoc.value) || pdfDoc.value !== doc || isDestroyed.value) {
      return
    }

    // Get page from document - use the stored reference
    // Wrap in try-catch to handle potential document corruption
    let page
    try {
      // Verify document still has getPage method before calling
      if (typeof doc.getPage !== 'function') {
        throw new Error('PDF document getPage method is not available')
      }

      page = await doc.getPage(pageNum)
    } catch (getPageError: any) {
      // If getPage fails with the specific private member error, document is corrupted
      const errorMessage = getPageError?.message || String(getPageError)
      const isCorruptionError =
        errorMessage.includes('private member') ||
        errorMessage.includes('#pagePromises') ||
        errorMessage.includes('class did not declare')

      console.error('Failed to get page from PDF document:', getPageError)

      if (isCorruptionError || !isPdfDocValid(pdfDoc.value)) {
        // Document is corrupted - clear it and show error
        error.value = 'PDF document became invalid. Reloading...'
        pdfDoc.value = null
        numPages.value = 0
        currentPage.value = 1

        // Attempt to reload the PDF after a short delay
        setTimeout(() => {
          if (!isDestroyed.value) {
            loadPdf()
          }
        }, 500)
        return
      }

      // Re-throw if it's not a document corruption issue
      throw getPageError
    }

    // Check again after async operation - verify document hasn't changed
    if (
      !isPdfDocValid(pdfDoc.value) ||
      pdfDoc.value !== doc ||
      !canvasRef.value ||
      isDestroyed.value
    ) {
      try {
        if (page && typeof page.cleanup === 'function') {
          page.cleanup()
        }
      } catch {
        // Ignore cleanup errors
      }
      return
    }

    const viewport = page.getViewport({ scale: 1.0 })
    const canvas = canvasRef.value
    const context = canvas.getContext('2d')

    if (!context || isDestroyed.value) return

    canvas.height = viewport.height
    canvas.width = viewport.width

    const renderContext = {
      canvasContext: context,
      viewport
    }

    // Store render task so we can cancel it if needed
    const task = page.render(renderContext)
    renderTask.value = task

    await task.promise

    // Clean up render task
    renderTask.value = null

    // Final check before updating state - verify document is still the same
    if (!isDestroyed.value && isPdfDocValid(pdfDoc.value) && pdfDoc.value === doc) {
      currentPage.value = pageNum
      error.value = null // Clear any previous errors on success
    }
  } catch (err) {
    // Don't set error if operation was cancelled or component destroyed
    if (isDestroyed.value) return

    // Check if it's a cancellation error
    if (err instanceof Error && err.name === 'RenderingCancelledException') {
      return
    }

    // Check if document is still valid after error
    if (!isPdfDocValid(pdfDoc.value)) {
      error.value = 'PDF document became invalid. Please reload the PDF.'
      pdfDoc.value = null
      numPages.value = 0
    } else {
      error.value = err instanceof Error ? err.message : 'Failed to render PDF page'
    }

    console.error('PDF rendering error:', err)
  }
}

const nextPage = () => {
  if (
    currentPage.value < numPages.value &&
    isPdfDocValid(pdfDoc.value) &&
    !isDestroyed.value
  ) {
    renderPage(currentPage.value + 1)
  }
}

const previousPage = () => {
  if (currentPage.value > 1 && isPdfDocValid(pdfDoc.value) && !isDestroyed.value) {
    renderPage(currentPage.value - 1)
  }
}

const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.25, 3.0)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.25, 0.5)
}

watch(
  () => props.url,
  () => {
    // Reset state when URL changes
    currentPage.value = 1
    scale.value = 1.0
    numPages.value = 0
    loadPdf()
  },
  { immediate: false }
)

onMounted(() => {
  if (isClient) {
    loadPdf()
  }
})

onBeforeUnmount(() => {
  isDestroyed.value = true

  // Cancel render task
  if (renderTask.value) {
    try {
      renderTask.value.cancel()
    } catch {
      // Ignore cancellation errors
    }
    renderTask.value = null
  }

  // Cancel loading task
  if (loadingTask.value) {
    try {
      loadingTask.value.destroy()
    } catch {
      // Ignore cancellation errors
    }
    loadingTask.value = null
  }

  // Destroy document
  if (pdfDoc.value) {
    try {
      pdfDoc.value.destroy()
    } catch {
      // Ignore destroy errors
    }
    pdfDoc.value = null
  }
})
</script>
