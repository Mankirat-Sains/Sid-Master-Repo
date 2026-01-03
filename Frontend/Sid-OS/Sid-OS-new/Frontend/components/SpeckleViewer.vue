<template>
  <div 
    v-if="visible"
    class="speckle-viewer-container relative bg-slate-900 border border-slate-700 rounded-lg overflow-hidden shadow-2xl"
    :style="{ width: width, height: heightStyle }"
  >
    <!-- Viewer Toolbar -->
    <div class="absolute top-0 left-0 right-0 bg-slate-800/95 backdrop-blur-sm border-b border-slate-700 px-4 py-2 flex items-center justify-between z-20">
      <div class="flex items-center gap-2">
        <button
          @click="$emit('close')"
          class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Close
        </button>
        <span v-if="modelName" class="text-sm text-slate-300 px-3 py-1 bg-slate-700 rounded-lg">
          {{ modelName }}
        </span>
      </div>
      
      <div class="flex items-center gap-2">
        <!-- Zoom Controls -->
        <button
          @click="zoomFit"
          class="p-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          title="Zoom to Fit"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
          </svg>
        </button>
        <button
          @click="zoomIn"
          class="p-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          title="Zoom In"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35M11 8v6M8 11h6" />
          </svg>
        </button>
        <button
          @click="zoomOut"
          class="p-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          title="Zoom Out"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35M8 11h6" />
          </svg>
        </button>
        <div class="w-px h-6 bg-slate-600"></div>
        <!-- View Controls -->
        <button
          @click="setView('top')"
          class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-medium transition-colors"
        >
          Top
        </button>
        <button
          @click="setView('front')"
          class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-medium transition-colors"
        >
          Front
        </button>
        <button
          @click="setView('3d')"
          class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-medium transition-colors"
        >
          3D
        </button>
        <div class="w-px h-6 bg-slate-600"></div>
        <!-- Section Tool -->
        <button
          @click="toggleSections"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
            sectionsEnabled 
              ? 'bg-purple-600 hover:bg-purple-700 text-white' 
              : 'bg-slate-700 hover:bg-slate-600 text-white'
          ]"
          title="Toggle Section Cutting"
        >
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Sections
        </button>
        <!-- Measurements Tool -->
        <button
          @click="toggleMeasurements"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
            measurementsEnabled 
              ? 'bg-purple-600 hover:bg-purple-700 text-white' 
              : 'bg-slate-700 hover:bg-slate-600 text-white'
          ]"
          title="Toggle Measurements"
        >
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          Measure
        </button>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="loading"
      class="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-10"
    >
      <div class="text-center">
        <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-white font-medium">{{ loadingMessage }}</p>
        <p v-if="loadingProgress > 0" class="text-slate-400 text-sm mt-2">{{ loadingProgress }}%</p>
      </div>
    </div>

    <!-- Viewer Canvas Container -->
    <div
      ref="viewerContainer"
      class="absolute inset-0"
      :style="{ top: '48px', width: '100%', height: 'calc(100% - 48px)' }"
    ></div>

    <!-- Object Info Panel (Bottom Right) -->
    <div
      v-if="selectedObject"
      class="absolute bottom-4 right-4 bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-lg shadow-xl p-4 max-w-sm z-20"
    >
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-white font-semibold text-sm">Selected Object</h4>
        <button
          @click="selectedObject = null"
          class="text-slate-400 hover:text-white transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="space-y-2 text-xs">
        <div v-if="selectedObject.id" class="flex justify-between">
          <span class="text-slate-400">ID:</span>
          <span class="text-white font-mono">{{ selectedObject.id }}</span>
        </div>
        <div v-if="selectedObject.type" class="flex justify-between">
          <span class="text-slate-400">Type:</span>
          <span class="text-white">{{ selectedObject.type }}</span>
        </div>
        <div v-if="selectedObject.name" class="flex justify-between">
          <span class="text-slate-400">Name:</span>
          <span class="text-white">{{ selectedObject.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRuntimeConfig } from '#app'

interface Props {
  modelUrl?: string
  modelName?: string
  visible?: boolean
  width?: string
  height?: string
  serverUrl?: string
  token?: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: true,
  width: '100%',
  height: '600px',
  serverUrl: 'https://app.speckle.systems'
})

// Compute height style - if height is 100%, use 100% (parent container handles sizing)
const heightStyle = computed(() => {
  return props.height
})

const emit = defineEmits<{
  close: []
  loaded: [url: string]
  error: [error: Error]
}>()

const config = useRuntimeConfig()
const viewerContainer = ref<HTMLElement | null>(null)
const loading = ref(false)
const loadingMessage = ref('Loading model...')
const loadingProgress = ref(0)
const selectedObject = ref<any>(null)
const sectionsEnabled = ref(false)
const measurementsEnabled = ref(false)

let viewer: any = null
let viewerModule: any = null
let viewerExtensions: any = {}

onMounted(async () => {
  if (props.modelUrl) {
    await loadModel(props.modelUrl)
  }
})

watch(() => props.modelUrl, async (newUrl, oldUrl) => {
  // Only load if URL actually changed and is visible
  if (newUrl && newUrl !== oldUrl && props.visible) {
    await loadModel(newUrl)
  }
})

watch(() => props.visible, async (isVisible) => {
  if (isVisible && props.modelUrl && !viewer) {
    await nextTick()
    await loadModel(props.modelUrl)
  }
  
  if (viewer && isVisible) {
    // Resize viewer when shown
    setTimeout(() => {
      viewer?.resize()
    }, 100)
  }
})

async function clearViewer() {
  if (!viewer) return
  
  try {
    // Use the viewer's built-in unloadAll method (same as Electron app)
    if (typeof viewer.unloadAll === 'function') {
      await viewer.unloadAll()
      console.log('✅ Viewer cleared using unloadAll()')
    } else {
      // Fallback to manual clearing if unloadAll doesn't exist
      console.warn('⚠️ viewer.unloadAll() not available, using manual clear')
      const worldTree = viewer.getWorldTree()
      if (worldTree && worldTree.root) {
        const childrenToRemove = [...(worldTree.root.children || [])]
        childrenToRemove.forEach(child => {
          try {
            if (child.model && child.model.id) {
              worldTree.removeObject(child.model.id)
            }
          } catch (e) {
            console.warn('Error removing object from world tree:', e)
          }
        })
      }
    }
    
    // Clear selection
    if (viewerExtensions.selection) {
      viewerExtensions.selection.clearSelection()
    }
    
    selectedObject.value = null
  } catch (error) {
    console.warn('⚠️ Error clearing viewer:', error)
  }
}

async function loadModel(url: string) {
  if (!viewerContainer.value) {
    console.error('❌ Viewer container not found')
    return
  }

  console.log('📦 Container element:', viewerContainer.value)
  console.log('📦 Container dimensions:', {
    width: viewerContainer.value.offsetWidth,
    height: viewerContainer.value.offsetHeight
  })

  try {
    loading.value = true
    loadingMessage.value = 'Clearing previous model...'
    loadingProgress.value = 0
    
    // Clear existing model before loading new one (same approach as Electron app)
    if (viewer) {
      await clearViewer()
      loadingMessage.value = 'Loading new model...'
    }

    console.log('📥 Importing @speckle/viewer...')
    // Dynamically import @speckle/viewer
    viewerModule = await import('@speckle/viewer')
    console.log('✅ @speckle/viewer imported successfully')
    
    const {
      Viewer,
      DefaultViewerParams,
      HybridCameraController,
      SelectionExtension,
      MeasurementsExtension,
      FilteringExtension,
      SectionTool,
      SectionOutlines,
      SpeckleLoader,
      UrlHelper,
      LoaderEvent
    } = viewerModule
    
    console.log('📦 Checking available exports...', {
      hasSpeckleLoader: !!SpeckleLoader,
      hasUrlHelper: !!UrlHelper,
      hasLoaderEvent: !!LoaderEvent,
      allKeys: Object.keys(viewerModule).filter(k => k.includes('Loader') || k.includes('Url') || k.includes('Helper'))
    })

    // Initialize viewer if not already created
    if (!viewer) {
      const viewerParams = {
        ...DefaultViewerParams,
        showStats: false,
        verbose: false
      }

      viewer = new Viewer(viewerContainer.value, viewerParams)
      await viewer.init()
      
      // Don't manually start render loop - the viewer handles this automatically
      // Manual render loops can cause glitchiness and performance issues
      // The viewer's built-in render loop is optimized and handles everything
      
      // Ensure viewer container has dimensions
      if (viewerContainer.value) {
        const rect = viewerContainer.value.getBoundingClientRect()
        console.log('📐 Viewer container dimensions:', {
          width: rect.width,
          height: rect.height,
          offsetWidth: viewerContainer.value.offsetWidth,
          offsetHeight: viewerContainer.value.offsetHeight
        })
        
        // If container has no dimensions, set a default
        if (rect.width === 0 || rect.height === 0) {
          console.warn('⚠️ Viewer container has zero dimensions, setting defaults')
          viewerContainer.value.style.width = '100%'
          viewerContainer.value.style.height = '600px'
        }
      }

      // Create extensions (same as Electron app)
      // Note: Don't explicitly set enabled=true - extensions are enabled by default
      // Only disable/enable when user toggles features to avoid performance issues
      viewerExtensions.cameraController = viewer.createExtension(HybridCameraController)
      viewerExtensions.selection = viewer.createExtension(SelectionExtension)
      
      // Only create extensions we actually need - measurements and filtering can be heavy
      // Create them but keep them disabled by default (like Electron app does)
      viewerExtensions.measurements = viewer.createExtension(MeasurementsExtension)
      if (viewerExtensions.measurements) {
        viewerExtensions.measurements.enabled = false // Disabled by default for performance
      }
      
      viewerExtensions.filtering = viewer.createExtension(FilteringExtension)
      // Filtering is enabled by default but lightweight, keep it enabled
      
      // Section Tool extensions (for cutting planes/sections)
      if (SectionTool) {
        viewerExtensions.sections = viewer.createExtension(SectionTool)
        // Sections disabled by default (user activates via button)
        if (viewerExtensions.sections) {
          viewerExtensions.sections.enabled = false
        }
      }
      if (SectionOutlines) {
        viewerExtensions.sectionOutlines = viewer.createExtension(SectionOutlines)
      }
      
      // Debug: Log extension status
      console.log('✅ Extensions created and enabled:')
      console.log('  📹 Camera Controller:', viewerExtensions.cameraController?.enabled)
      console.log('  🖱️ Selection:', viewerExtensions.selection?.enabled)
      console.log('  📏 Measurements:', viewerExtensions.measurements?.enabled)
      console.log('  🔍 Filtering:', viewerExtensions.filtering?.enabled)
      console.log('  ✂️ Sections:', viewerExtensions.sections?.enabled)
      console.log('  📐 Section Outlines:', viewerExtensions.sectionOutlines?.enabled)
      
      // Log available camera controller methods for debugging
      if (viewerExtensions.cameraController) {
        console.log('🎥 Camera Controller methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(viewerExtensions.cameraController)))
        console.log('🎥 Camera Controller properties:', Object.keys(viewerExtensions.cameraController))
      }

      // Set up event listeners
      viewer.on(viewerModule.ViewerEvent.LoadComplete, (resourceUrl: string) => {
        console.log('✅ Model loaded successfully:', resourceUrl)
        loading.value = false
        loadingProgress.value = 100
        
        // Just resize - viewer handles rendering automatically
        // Don't manually call render() as it interferes with the viewer's render loop
        setTimeout(() => {
          if (viewer) {
            viewer.resize()
          }
        }, 50)
        
        emit('loaded', resourceUrl)
      })

      viewer.on(viewerModule.ViewerEvent.LoadProgress, (progress: number) => {
        console.log('📊 Load progress:', progress)
        loadingProgress.value = Math.round(progress * 100)
      })

      viewer.on(viewerModule.ViewerEvent.LoadError, (error: any) => {
        console.error('❌ Viewer load error event:', error)
        loading.value = false
        loadingMessage.value = `Load error: ${error.message || 'Unknown error'}`
        emit('error', error)
      })

      viewer.on(viewerModule.ViewerEvent.ObjectClicked, (event: any) => {
        if (event?.hits?.[0]?.node) {
          const node = event.hits[0].node
          selectedObject.value = {
            id: node.model.id,
            type: node.model.raw?.speckle_type || 'Unknown',
            name: node.model.raw?.name || null,
            ...node.model.raw
          }
          viewerExtensions.selection?.selectObjects([node.model.id])
        } else {
          selectedObject.value = null
          viewerExtensions.selection?.clearSelection()
        }
      })
    }

    // Load the model using SpeckleLoader
    loadingMessage.value = 'Getting resource URLs...'
    console.log('🔄 Attempting to load model from URL:', url)
    
    // Verify SpeckleLoader and UrlHelper are available
    if (!SpeckleLoader || !UrlHelper) {
      const error = new Error(`SpeckleLoader or UrlHelper not found. SpeckleLoader: ${!!SpeckleLoader}, UrlHelper: ${!!UrlHelper}`)
      console.error('❌', error.message)
      console.error('Available exports:', Object.keys(viewerModule))
      loading.value = false
      loadingMessage.value = 'Error: SpeckleLoader or UrlHelper not available'
      emit('error', error)
      return
    }
    
    console.log('✅ SpeckleLoader and UrlHelper available')
    
    try {
      
      // Get the auth token from props or config
      // In Nuxt, environment variables are exposed via runtimeConfig
      // IMPORTANT: Nuxt must be restarted after changing .env files for changes to take effect!
      let token = props.token || config.public.speckleToken || ''
      
      console.log('🔐 Token loading check:', {
        hasPropsToken: !!props.token,
        configTokenExists: !!config.public.speckleToken,
        configTokenLength: config.public.speckleToken?.length || 0,
        configTokenPreview: config.public.speckleToken ? `${config.public.speckleToken.substring(0, 10)}...${config.public.speckleToken.substring(config.public.speckleToken.length - 4)}` : 'none',
        finalTokenExists: !!token,
        finalTokenLength: token?.length || 0
      })
      
      // Debug: Log the full config to see what's available
      console.log('🔍 Full runtime config (speckle-related):', {
        speckleUrl: config.public.speckleUrl,
        speckleTokenLength: config.public.speckleToken?.length || 0,
        speckleTokenPreview: config.public.speckleToken ? `${config.public.speckleToken.substring(0, 15)}...` : 'undefined'
      })
      
      // Clean the token (trim whitespace, remove quotes) - like Electron app does
      if (token) {
        token = token.trim()
        token = token.replace(/^["']|["']$/g, '') // Remove surrounding quotes
      }
      
      // Extract server URL from the model URL
      // Format: http://server/projects/projectId/models/modelId
      const urlMatch = url.match(/^(https?:\/\/[^\/]+)/)
      const serverUrl = urlMatch ? urlMatch[1] : props.serverUrl || config.public.speckleUrl
      
      console.log('📦 Getting resource URLs...', {
        url: url,
        serverUrl: serverUrl,
        hasToken: !!token,
        tokenLength: token?.length || 0,
        tokenPreview: token ? `${token.substring(0, 10)}...${token.substring(token.length - 10)}` : 'none',
        urlFormat: url.match(/\/projects\/([^\/]+)\/models\/([^\/]+)/) ? 'valid' : 'invalid'
      })
      
      // Warn if no token is available
      if (!token) {
        console.warn('⚠️ No authentication token found! Private models may fail to load.')
        console.warn('💡 Make sure SPECKLE_TOKEN is set in your .env file')
        console.warn('💡 Token should be accessible via config.public.speckleToken')
      }
      
      // Verify URL format is correct
      const urlParts = url.match(/\/projects\/([^\/]+)\/models\/([^\/]+)/)
      if (!urlParts) {
        throw new Error('Invalid Speckle URL format. Expected: http://server/projects/projectId/models/modelId')
      }
      
      console.log('✅ URL format valid:', {
        projectId: urlParts[1],
        modelId: urlParts[2]
      })
      
      // Get resource URLs from the model URL
      // Note: UrlHelper makes GraphQL queries to the Speckle server
      // The URL format should be: http://server/projects/projectId/models/modelId
      let objectUrls
      try {
        // Try using UrlHelper.getResourceUrls - this makes GraphQL queries
        console.log('🔍 Calling UrlHelper.getResourceUrls...')
        objectUrls = await UrlHelper.getResourceUrls(url, token || undefined)
        console.log('✅ UrlHelper.getResourceUrls succeeded')
      } catch (urlError: any) {
        console.error('❌ Error getting resource URLs:', urlError)
        console.error('Error details:', {
          message: urlError.message,
          stack: urlError.stack,
          url: url,
          hasToken: !!token,
          serverUrl: serverUrl
        })
        
        // Check for specific error types
        if (urlError.message && (urlError.message.includes('403') || urlError.message.includes('Forbidden'))) {
          throw new Error('Authentication error: Token may not have access to this project')
        } else if (urlError.message && urlError.message.includes('404')) {
          throw new Error('Model not found: Check if the project/model ID is correct')
        } else if (urlError.message && urlError.message.includes('Query failed') || urlError.message.includes('fetch')) {
          // This might be a CORS issue - try to provide helpful error message
          console.warn('⚠️ Query failed - this might be a CORS issue')
          console.warn('💡 The Speckle server needs to allow CORS from your origin')
          console.warn('💡 Electron apps don\'t have CORS restrictions, but browsers do')
          throw new Error(`Query failed: ${urlError.message}. This might be a CORS issue - the Speckle server needs to allow requests from ${window.location.origin}`)
        }
        throw urlError
      }
      
      if (!objectUrls || objectUrls.length === 0) {
        throw new Error('No object URLs found for this model')
      }
      
      console.log(`📍 Found ${objectUrls.length} object URL(s) to load`)
      
      // Load each object URL
      for (const objUrl of objectUrls) {
        console.log('⬇️ Loading object:', objUrl.substring(0, 80) + '...')
        loadingMessage.value = `Loading object ${objectUrls.indexOf(objUrl) + 1} of ${objectUrls.length}...`
        
        // Create the loader
        // Note: SpeckleLoader signature: (worldTree, objectUrl, authToken, enableCache)
        console.log('🔧 Creating SpeckleLoader with:', {
          objectUrl: objUrl.substring(0, 80) + '...',
          hasToken: !!token,
          tokenLength: token?.length || 0
        })
        
        const loader = new SpeckleLoader(
          viewer.getWorldTree(), // The viewer's world tree
          objUrl, // The object URL to load
          token || undefined, // Auth token (pass undefined if empty, not empty string)
          true // Enable caching
        )
        
        // Track loading progress
        loader.on(LoaderEvent.LoadProgress, (args: any) => {
          const progress = args.progress * 100
          loadingProgress.value = Math.round(progress)
          console.log(`📊 Loading progress: ${loadingProgress.value}%`)
        })
        
        // Load the object (true = zoom to fit after loading)
        // Like the Electron app, we let loadObject handle zoom and rendering
        await viewer.loadObject(loader, true)
        console.log('✅ Object loaded successfully')
      }
      
      console.log('✅ All objects loaded successfully')
      
      // Like the Electron app: just ensure resize, let the viewer handle rendering
      // Don't do extra zoom or render operations - loadObject already handled it
      if (viewer) {
        setTimeout(() => {
          viewer.resize()
        }, 100)
      }
      
    } catch (loadError: any) {
      console.error('❌ Error loading model:', loadError)
      loading.value = false
      
      // Check for CORS errors specifically
      if (loadError.message && (loadError.message.includes('CORS') || loadError.message.includes('Access-Control-Allow-Origin'))) {
        loadingMessage.value = 'CORS Error: The Speckle server needs to allow requests from your origin. This is a server configuration issue.'
        console.error('🚫 CORS Error Detected')
        console.error('💡 Solution: Configure the Speckle server to allow CORS from:', window.location.origin)
        console.error('💡 The server needs to send: Access-Control-Allow-Origin: ' + window.location.origin)
        console.error('💡 This is why it works in Electron (no CORS) but fails in browsers')
      } else if (loadError.message && (loadError.message.includes('403') || loadError.message.includes('Forbidden'))) {
        loadingMessage.value = 'Authentication error: Check if your token has access to this project'
      } else {
        loadingMessage.value = `Error: ${loadError.message || 'Failed to load model'}`
      }
      
      emit('error', loadError)
    }
    
  } catch (error: any) {
    console.error('❌ Error in loadModel function:', error)
    console.error('Error stack:', error.stack)
    loading.value = false
    loadingMessage.value = `Error: ${error.message || 'Unknown error occurred'}`
    emit('error', error)
  }
}

function zoomFit() {
  if (!viewerExtensions.cameraController || !viewer) return
  
  try {
    const renderer = viewer.getRenderer()
    if (!renderer) return
    
    const sceneBox = renderer.sceneBox
    if (!sceneBox) return
    
    // Use setCameraView with the scene bounds (Box3) to fit the view
    // According to Speckle docs: setCameraView(bounds: Box3, transition: boolean, fit?: number)
    if (typeof (viewerExtensions.cameraController as any).setCameraView === 'function') {
      (viewerExtensions.cameraController as any).setCameraView(sceneBox, true)
      console.log('✅ Zoom to fit completed')
      return
    }
    
    console.warn('⚠️ setCameraView method not found for zoom fit')
  } catch (error) {
    console.error('Error in zoomFit:', error)
  }
}

function zoomIn() {
  // Note: Speckle viewer uses mouse wheel and controls for zoom
  // These functions can trigger zoom via the controls if available
  // For now, we'll use a simple approach that works with the camera controller
  if (!viewerExtensions.cameraController || !viewer) return
  
  try {
    // Try to access the controls and trigger zoom in
    const controls = (viewerExtensions.cameraController as any).controls
    if (controls && typeof controls.zoomIn === 'function') {
      controls.zoomIn()
      return
    }
    
    // Alternative: Use the camera's position if controls don't have zoomIn
    const camera = (viewerExtensions.cameraController as any).renderingCamera
    if (camera && camera.position) {
      // Zoom in by moving camera closer (multiply position by factor < 1)
      camera.position.multiplyScalar(0.9)
    }
  } catch (error) {
    console.error('Error in zoomIn:', error)
  }
}

function zoomOut() {
  // Note: Speckle viewer uses mouse wheel and controls for zoom
  if (!viewerExtensions.cameraController || !viewer) return
  
  try {
    // Try to access the controls and trigger zoom out
    const controls = (viewerExtensions.cameraController as any).controls
    if (controls && typeof controls.zoomOut === 'function') {
      controls.zoomOut()
      return
    }
    
    // Alternative: Use the camera's position if controls don't have zoomOut
    const camera = (viewerExtensions.cameraController as any).renderingCamera
    if (camera && camera.position) {
      // Zoom out by moving camera farther (multiply position by factor > 1)
      camera.position.multiplyScalar(1.1)
    }
  } catch (error) {
    console.error('Error in zoomOut:', error)
  }
}

function setView(view: 'top' | 'front' | '3d') {
  if (!viewerExtensions.cameraController) {
    console.warn('Camera controller not available')
    return
  }
  
  try {
    console.log('🔍 Setting view to:', view)
    
    // Use the proper CameraController API from Speckle documentation
    // setCameraView accepts canonical views: 'front', 'top', '3d', etc.
    // Signature: setCameraView(view: CanonicalView, transition: boolean, fit?: number)
    if (typeof (viewerExtensions.cameraController as any).setCameraView === 'function') {
      // Map our view names to canonical view names
      let canonicalView: string = view
      if (view === '3d') {
        canonicalView = '3D' // Speckle uses '3D' not '3d'
      }
      
      // Call setCameraView with transition=true for smooth animation
      (viewerExtensions.cameraController as any).setCameraView(canonicalView, true)
      console.log('✅ View set to:', canonicalView)
      return
    }
    
    console.warn('⚠️ setCameraView method not found on camera controller')
    console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(viewerExtensions.cameraController)))
    
  } catch (error) {
    console.error('❌ Error setting view:', error)
  }
}

function toggleSections() {
  if (!viewerExtensions.sections) {
    console.warn('Sections extension not available')
    return
  }
  
  try {
    // Toggle the section tool
    if (typeof (viewerExtensions.sections as any).toggle === 'function') {
      (viewerExtensions.sections as any).toggle()
      sectionsEnabled.value = !sectionsEnabled.value
      console.log('✅ Sections toggled:', sectionsEnabled.value)
    } else if (typeof (viewerExtensions.sections as any).enabled !== 'undefined') {
      // Fallback: toggle enabled property
      viewerExtensions.sections.enabled = !viewerExtensions.sections.enabled
      sectionsEnabled.value = viewerExtensions.sections.enabled
      console.log('✅ Sections enabled:', sectionsEnabled.value)
    }
  } catch (error) {
    console.error('❌ Error toggling sections:', error)
  }
}

function toggleMeasurements() {
  if (!viewerExtensions.measurements) {
    console.warn('Measurements extension not available')
    return
  }
  
  try {
    // Toggle the measurements tool
    if (typeof (viewerExtensions.measurements as any).toggle === 'function') {
      (viewerExtensions.measurements as any).toggle()
      measurementsEnabled.value = !measurementsEnabled.value
      console.log('✅ Measurements toggled:', measurementsEnabled.value)
    } else if (typeof (viewerExtensions.measurements as any).enabled !== 'undefined') {
      // Fallback: toggle enabled property
      viewerExtensions.measurements.enabled = !viewerExtensions.measurements.enabled
      measurementsEnabled.value = viewerExtensions.measurements.enabled
      console.log('✅ Measurements enabled:', measurementsEnabled.value)
    }
  } catch (error) {
    console.error('❌ Error toggling measurements:', error)
  }
}

onBeforeUnmount(() => {
  if (viewer) {
    viewer.dispose()
    viewer = null
  }
})
</script>

<style scoped>
.speckle-viewer-container {
  min-height: 400px;
}
</style>
