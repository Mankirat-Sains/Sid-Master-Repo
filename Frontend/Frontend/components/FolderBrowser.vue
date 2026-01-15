<template>
  <div class="h-full flex flex-col bg-[#0f0f0f] text-white">
    <!-- Current Path Breadcrumb -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-white/10 bg-[#111]">
      <div class="flex items-center gap-2 text-sm">
        <button
          v-if="canNavigateUp"
          @click="navigateUp"
          class="px-2 py-1 rounded hover:bg-white/10 text-white/60 hover:text-white transition flex items-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <span class="text-white/60 truncate flex-1" :title="currentPath">{{ currentPath || 'Select a location' }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center space-y-3">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent mx-auto"></div>
        <p class="text-white/60">Loading folders...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center space-y-3 p-4">
        <svg class="w-12 h-12 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="text-red-400 text-sm mb-2">{{ error }}</p>
        <p class="text-white/40 text-xs mb-1">Trying to connect to: {{ agentApiUrl.value }}/api/agent/files/list</p>
        <p class="text-white/40 text-xs">Make sure the desktop agent is running on port 8001</p>
        <button
          @click="loadFolders"
          class="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Folder List -->
    <div v-else class="flex-1 overflow-y-auto px-4 py-2">
      <div v-if="items.length === 0" class="text-center py-12 text-white/60">
        <svg class="w-12 h-12 mx-auto mb-3 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <p>No folders found</p>
      </div>
      <div v-else class="space-y-1">
        <!-- Folders -->
        <div
          v-for="item in folders"
          :key="item.path"
          @click="navigateToFolder(item.path)"
          @dblclick="selectFolder(item.path)"
          :class="[
            'flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition group',
            selectedFolder === item.path 
              ? 'bg-purple-600/20 border-purple-500/40' 
              : 'bg-white/5 hover:bg-white/10 border-transparent hover:border-white/10'
          ]"
        >
          <svg class="w-5 h-5 text-purple-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <span class="flex-1 text-white group-hover:text-purple-300 transition truncate">{{ item.name }}</span>
          <svg class="w-4 h-4 text-white/40 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <!-- Files (show but dimmed) -->
        <div
          v-for="item in files"
          :key="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/3 border border-transparent opacity-50"
        >
          <svg class="w-5 h-5 text-white/40 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="flex-1 text-white/60 truncate">{{ item.name }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Navigation -->
    <div class="flex-shrink-0 px-4 py-3 border-t border-white/10 bg-[#111]">
      <p class="text-xs text-white/40 mb-2">Quick Navigation</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="location in quickLocations"
          :key="location.path"
          @click="navigateToFolder(location.path)"
          class="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white text-sm transition"
        >
          {{ location.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

interface FolderItem {
  name: string
  path: string
  is_directory: boolean
  size_bytes?: number
  modified_at?: string
}

const props = defineProps<{
  initialPath?: string
}>()

const emit = defineEmits<{
  'path-change': [path: string]
  'folder-selected': [path: string]
}>()

const config = useRuntimeConfig()
const agentApiUrl = computed(() => config.public.agentApiUrl || 'http://localhost:8001')

const currentPath = ref(props.initialPath || '/Volumes')
const items = ref<FolderItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedFolder = ref<string | null>(null)

const folders = computed(() => items.value.filter(item => item.is_directory))
const files = computed(() => items.value.filter(item => !item.is_directory))

const canNavigateUp = computed(() => {
  const parts = currentPath.value.split('/').filter(p => p)
  return parts.length > 0
})

const quickLocations = [
  { name: 'Volumes', path: '/Volumes' },
  { name: 'Home', path: '/Users' },
  { name: 'Desktop', path: '~/Desktop' },
  { name: 'Documents', path: '~/Documents' }
]

async function loadFolders() {
  loading.value = true
  error.value = null
  
  try {
    const response = await $fetch<{
      directory: string
      count: number
      items: FolderItem[]
    }>(`${agentApiUrl.value}/api/agent/files/list`, {
      params: { directory: currentPath.value }
    })

    items.value = response.items
    emit('path-change', currentPath.value)
  } catch (err: any) {
    console.error('Error loading folders:', err)
    if (err.statusCode === 404 || err.message?.includes('404')) {
      error.value = `Desktop agent not found at ${agentApiUrl.value}. Make sure the agent is running on port 8001.`
    } else if (err.statusCode === 500 || err.message?.includes('500')) {
      error.value = 'Server error. Check that the directory path is valid and accessible.'
    } else {
      error.value = err.message || `Failed to connect to desktop agent at ${agentApiUrl.value}. Is it running?`
    }
  } finally {
    loading.value = false
  }
}

function navigateToFolder(path: string) {
  // Handle ~ for home directory
  if (path.startsWith('~')) {
    // This will be resolved by the backend
  }
  currentPath.value = path
  selectedFolder.value = null
}

function navigateUp() {
  const parts = currentPath.value.split('/').filter(p => p)
  if (parts.length > 1) {
    currentPath.value = '/' + parts.slice(0, -1).join('/')
  } else if (parts.length === 1) {
    currentPath.value = '/'
  }
  selectedFolder.value = null
}

function selectFolder(path: string) {
  selectedFolder.value = path
  emit('folder-selected', path)
}

watch(currentPath, () => {
  loadFolders()
})

onMounted(() => {
  loadFolders()
})
</script>
