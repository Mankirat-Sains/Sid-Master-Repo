<template>
  <div class="h-full flex flex-col text-white">
    <!-- Loading State -->
    <div v-if="loading && items.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-center space-y-3">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-purple-500 border-t-transparent mx-auto"></div>
        <p class="text-white/60 text-sm">Loading files...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center p-4">
      <div class="text-center space-y-2">
        <p class="text-red-400 text-sm">{{ error }}</p>
        <button
          @click="loadItems"
          class="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-sm transition"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- File Tree -->
    <div v-else class="flex-1 overflow-y-auto py-2">
      <div v-if="items.length === 0" class="text-center py-8 text-white/40 text-sm">
        No files found
      </div>
      <div v-else>
        <FileTreeNode
          v-for="item in items"
          :key="item.path"
          :item="item"
          :selected-files="selectedFiles"
          :expanded-folders="expandedFolders"
          :depth="0"
          @file-click="handleFileClick"
          @toggle-folder="toggleFolder"
          @load-children="loadChildren"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import FileTreeNode from '~/components/FileTreeNode.vue'
import { useFileStatus } from '~/composables/useFileStatus'

export interface TreeItem {
  name: string
  path: string
  is_directory: boolean
  size_bytes?: number
  modified_at?: string
  children?: TreeItem[]
  childrenLoaded?: boolean
  inDatabase?: boolean
  streamId?: string
  models?: Array<{ id: string; name: string }>
}

const props = defineProps<{
  rootPath: string
  selectedFiles: Set<string>
}>()

const emit = defineEmits<{
  'file-click': [file: { name: string; path: string; streamId?: string; models?: Array<{ id: string; name: string }> }]
}>()

const config = useRuntimeConfig()
const agentApiUrl = config.public.agentApiUrl || 'http://localhost:8001'
const { getFileStreamInfo } = useFileStatus()

const items = ref<TreeItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const expandedFolders = ref<Set<string>>(new Set())

// Check file status for .rvt files
async function checkFileStatus(fileName: string): Promise<{ inDatabase: boolean; streamId?: string; models?: Array<{ id: string; name: string }> }> {
  // Only check .rvt files for now
  if (!fileName.toLowerCase().endsWith('.rvt')) {
    return { inDatabase: false }
  }
  
  try {
    const streamInfo = await getFileStreamInfo(fileName)
    if (streamInfo) {
      return {
        inDatabase: true,
        streamId: streamInfo.id,
        models: streamInfo.models
      }
    }
    return { inDatabase: false }
  } catch (err) {
    console.error('Error checking file status:', err)
    return { inDatabase: false }
  }
}

async function loadItems() {
  loading.value = true
  error.value = null
  
  try {
    const response = await $fetch<{
      directory: string
      count: number
      items: TreeItem[]
    }>(`${agentApiUrl}/api/agent/files/list`, {
      params: { directory: props.rootPath }
    })

    // Check status for all .rvt files
    const itemsWithStatus = await Promise.all(
      response.items.map(async (item) => {
        if (item.is_directory) {
          return {
            ...item,
            children: [],
            childrenLoaded: false
          }
        }
        
        // Check file status
        const status = await checkFileStatus(item.name)
        return {
          ...item,
          children: undefined,
          childrenLoaded: false,
          ...status
        }
      })
    )

    items.value = itemsWithStatus
  } catch (err: any) {
    console.error('Error loading file tree:', err)
    if (err.statusCode === 404 || err.message?.includes('404')) {
      error.value = `Desktop agent not found. Make sure the agent is running on port 8001.`
    } else {
      error.value = err.message || 'Failed to load files'
    }
  } finally {
    loading.value = false
  }
}

async function loadChildren(folderPath: string) {
  try {
    const response = await $fetch<{
      directory: string
      count: number
      items: TreeItem[]
    }>(`${agentApiUrl}/api/agent/files/list`, {
      params: { directory: folderPath }
    })

    // Check status for .rvt files in children
    const childrenWithStatus = await Promise.all(
      response.items.map(async (item) => {
        if (item.is_directory) {
          return {
            ...item,
            children: [],
            childrenLoaded: false
          }
        }
        
        const status = await checkFileStatus(item.name)
        return {
          ...item,
          children: undefined,
          childrenLoaded: false,
          ...status
        }
      })
    )

    // Find the folder in the tree and update its children
    updateFolderChildren(items.value, folderPath, childrenWithStatus)
  } catch (err: any) {
    console.error('Error loading folder children:', err)
  }
}

function updateFolderChildren(nodes: TreeItem[], folderPath: string, children: TreeItem[]) {
  for (const node of nodes) {
    if (node.path === folderPath) {
      node.children = children
      node.childrenLoaded = true
      return true
    }
    if (node.children && node.children.length > 0) {
      if (updateFolderChildren(node.children, folderPath, children)) {
        return true
      }
    }
  }
  return false
}

function toggleFolder(folderPath: string) {
  if (expandedFolders.value.has(folderPath)) {
    expandedFolders.value.delete(folderPath)
  } else {
    expandedFolders.value.add(folderPath)
  }
  // Force reactivity
  expandedFolders.value = new Set(expandedFolders.value)
}

function handleFileClick(file: { name: string; path: string }) {
  // Find the item in the tree to get stream info
  const findItem = (nodes: TreeItem[]): TreeItem | null => {
    for (const node of nodes) {
      if (node.path === file.path) {
        return node
      }
      if (node.children) {
        const found = findItem(node.children)
        if (found) return found
      }
    }
    return null
  }
  
  const item = findItem(items.value)
  emit('file-click', {
    name: file.name,
    path: file.path,
    streamId: item?.streamId,
    models: item?.models
  })
}

watch(() => props.rootPath, () => {
  loadItems()
})

onMounted(() => {
  loadItems()
})
</script>
