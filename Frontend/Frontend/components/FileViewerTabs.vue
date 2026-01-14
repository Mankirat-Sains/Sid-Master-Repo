<template>
  <div class="h-full flex flex-col bg-[#0a0a0a] text-white">
    <!-- Tabs Header -->
    <div class="flex-shrink-0 border-b border-white/10 bg-[#111]">
      <div class="flex items-center overflow-x-auto">
        <div
          v-for="file in files"
          :key="file.id"
          :class="[
            'flex items-center gap-2 px-4 py-2.5 border-r border-white/5 cursor-pointer transition group min-w-0',
            activeFileId === file.id 
              ? 'bg-[#0a0a0a] text-white border-b-2 border-b-purple-500' 
              : 'bg-[#111] text-white/60 hover:text-white hover:bg-white/5'
          ]"
          @click="$emit('select', file.id)"
        >
          <!-- File Icon -->
          <component :is="getFileIcon(file.type)" class="w-4 h-4 flex-shrink-0" :class="getIconClass(file.type)" />
          
          <!-- File Name -->
          <span class="truncate max-w-[120px] text-sm">{{ file.name }}</span>
          
          <!-- Close Button -->
          <button
            @click.stop="$emit('close', file.id)"
            class="w-4 h-4 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-white/10 transition"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Viewer Content -->
    <div class="flex-1 min-h-0 overflow-hidden">
      <template v-if="activeFile">
        <!-- Model Viewer -->
        <div v-if="activeFile.type === 'model'" class="h-full flex flex-col">
          <!-- Model Selector (if multiple models) -->
          <div v-if="activeFile.models && activeFile.models.length > 1" class="flex-shrink-0 px-4 py-3 border-b border-white/10 bg-[#111]">
            <div class="flex items-center gap-3">
              <label class="text-sm text-white/60">Model:</label>
              <select
                :value="activeFile.selectedModelId || activeFile.models[0]?.id"
                @change="handleModelSelect(activeFile.id, ($event.target as HTMLSelectElement).value)"
                class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-500/50 transition"
              >
                <option
                  v-for="model in activeFile.models"
                  :key="model.id"
                  :value="model.id"
                >
                  {{ model.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- Speckle Viewer -->
          <div v-if="modelUrl" class="flex-1 min-h-0">
            <SpeckleViewer
              :model-url="modelUrl"
              :model-name="activeFile.name"
              :visible="true"
              width="100%"
              height="100%"
              :server-url="config.public.speckleUrl"
              :token="config.public.speckleToken"
            />
          </div>

          <!-- Loading State -->
          <div v-else-if="loadingModel" class="flex-1 flex items-center justify-center">
            <div class="text-center space-y-3">
              <div class="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent mx-auto"></div>
              <p class="text-white/60">Loading model...</p>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="modelError" class="flex-1 flex items-center justify-center">
            <div class="text-center space-y-4 p-8">
              <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center">
                <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
                <p class="text-sm text-white/60 mt-1">3D Model File</p>
              </div>
              <p class="text-red-400 text-sm max-w-md">{{ modelError }}</p>
              <button
                v-if="activeFile.streamId"
                @click="loadModelForFile(activeFile)"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
              >
                Retry
              </button>
            </div>
          </div>

          <!-- No Stream Found -->
          <div v-else class="flex-1 flex items-center justify-center">
            <div class="text-center space-y-4 p-8">
              <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-yellow-500 to-yellow-700 flex items-center justify-center">
                <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
                <p class="text-sm text-white/60 mt-1">3D Model File</p>
              </div>
              <p class="text-white/40 text-sm max-w-md">
                This file is not in the database. Files must be uploaded to Speckle to be viewed.
              </p>
            </div>
          </div>
        </div>

        <!-- PDF Viewer -->
        <div v-else-if="activeFile.type === 'pdf'" class="h-full flex items-center justify-center">
          <div class="text-center space-y-4 p-8">
            <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
              <p class="text-sm text-white/60 mt-1">PDF Document</p>
            </div>
            <p class="text-white/40 text-sm max-w-md">
              PDF viewing coming soon. The file is located at:
            </p>
            <code class="text-xs text-white/50 bg-white/5 px-2 py-1 rounded block truncate max-w-md">
              {{ activeFile.path }}
            </code>
          </div>
        </div>

        <!-- Excel Viewer -->
        <div v-else-if="activeFile.type === 'excel'" class="h-full flex items-center justify-center">
          <div class="text-center space-y-4 p-8">
            <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
              <p class="text-sm text-white/60 mt-1">Excel Spreadsheet</p>
            </div>
            <p class="text-white/40 text-sm max-w-md">
              Excel viewing coming soon. The file is located at:
            </p>
            <code class="text-xs text-white/50 bg-white/5 px-2 py-1 rounded block truncate max-w-md">
              {{ activeFile.path }}
            </code>
          </div>
        </div>

        <!-- Image Viewer -->
        <div v-else-if="activeFile.type === 'image'" class="h-full flex items-center justify-center p-4">
          <div class="text-center space-y-4">
            <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
              <p class="text-sm text-white/60 mt-1">Image File</p>
            </div>
            <p class="text-white/40 text-sm">Image preview coming soon</p>
          </div>
        </div>

        <!-- Other Files -->
        <div v-else class="h-full flex items-center justify-center">
          <div class="text-center space-y-4 p-8">
            <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ activeFile.name }}</h3>
              <p class="text-sm text-white/60 mt-1">File</p>
            </div>
            <code class="text-xs text-white/50 bg-white/5 px-2 py-1 rounded block truncate max-w-md">
              {{ activeFile.path }}
            </code>
          </div>
        </div>
      </template>

      <!-- No File Selected -->
      <div v-else class="h-full flex items-center justify-center">
        <div class="text-center text-white/40">
          <p>Select a file to view</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, h } from 'vue'
import SpeckleViewer from '~/components/SpeckleViewer.vue'

interface OpenFile {
  id: string
  name: string
  path: string
  type: 'model' | 'pdf' | 'excel' | 'doc' | 'image' | 'other'
  streamId?: string
  models?: Array<{ id: string; name: string }>
  selectedModelId?: string
}

const props = defineProps<{
  files: OpenFile[]
  activeFileId: string | null
}>()

const emit = defineEmits<{
  close: [fileId: string]
  select: [fileId: string]
  'update-model': [fileId: string, modelId: string]
}>()

const config = useRuntimeConfig()
const modelUrl = ref<string | null>(null)
const loadingModel = ref(false)
const modelError = ref<string | null>(null)

const activeFile = computed(() => {
  if (!props.activeFileId) return null
  return props.files.find(f => f.id === props.activeFileId) || null
})

// Watch for active file changes and load model
watch([() => props.activeFileId, () => activeFile.value?.selectedModelId], () => {
  if (activeFile.value && activeFile.value.type === 'model') {
    loadModelForFile(activeFile.value)
  } else {
    modelUrl.value = null
    modelError.value = null
  }
}, { immediate: true })

async function loadModelForFile(file: OpenFile) {
  if (!file.streamId) {
    modelUrl.value = null
    modelError.value = null
    return
  }

  const modelId = file.selectedModelId || file.models?.[0]?.id
  if (!modelId) {
    modelError.value = 'No models available for this file'
    return
  }

  loadingModel.value = true
  modelError.value = null
  modelUrl.value = null

  try {
    // Construct the model URL
    const url = `${config.public.speckleUrl}/projects/${file.streamId}/models/${modelId}`
    modelUrl.value = url
  } catch (error: any) {
    console.error('Error loading model:', error)
    modelError.value = error.message || 'Failed to load model'
  } finally {
    loadingModel.value = false
  }
}

function handleModelSelect(fileId: string, modelId: string) {
  emit('update-model', fileId, modelId)
  
  // Update the file's selected model
  const file = props.files.find(f => f.id === fileId)
  if (file) {
    file.selectedModelId = modelId
    loadModelForFile(file)
  }
}

function getFileIcon(type: OpenFile['type']) {
  switch (type) {
    case 'model':
      return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' })
      ])
    case 'pdf':
      return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z' })
      ])
    case 'excel':
      return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' })
      ])
    case 'image':
      return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' })
      ])
    default:
      return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' })
      ])
  }
}

function getIconClass(type: OpenFile['type']) {
  switch (type) {
    case 'model': return 'text-green-400'
    case 'pdf': return 'text-red-400'
    case 'excel': return 'text-emerald-400'
    case 'image': return 'text-blue-400'
    default: return 'text-white/50'
  }
}
</script>
