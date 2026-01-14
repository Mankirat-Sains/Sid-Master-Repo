<template>
  <div class="h-full flex bg-[#0f0f0f] text-white overflow-hidden">
    <!-- Left Panel: File Tree -->
    <div 
      ref="leftPanelRef"
      class="flex-shrink-0 border-r border-white/10 flex flex-col bg-[#0a0a0a]"
      :style="{ width: `${leftPanelWidth}px` }"
    >
      <!-- Header -->
      <div class="flex-shrink-0 px-4 py-3 border-b border-white/10 bg-[#111]">
        <div class="flex items-center gap-2">
          <button
            @click="$emit('back')"
            class="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition flex items-center justify-center"
            title="Back to projects"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div class="flex-1 min-w-0">
            <h2 class="text-sm font-semibold text-white truncate">{{ projectName }}</h2>
            <p class="text-xs text-white/50 truncate" :title="rootPath">{{ rootPath }}</p>
          </div>
          <button
            @click="showStatistics = !showStatistics"
            :class="[
              'w-7 h-7 rounded-lg transition flex items-center justify-center',
              showStatistics 
                ? 'bg-purple-600 text-white' 
                : 'bg-white/5 hover:bg-white/10 text-white/60 hover:text-white'
            ]"
            title="Toggle statistics"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Statistics Panel (when toggled) -->
      <ProjectStatistics
        v-if="showStatistics"
        :project-id="projectId"
        :root-path="rootPath"
        @close="showStatistics = false"
        class="flex-1 overflow-hidden"
      />

      <!-- File Tree (when statistics not shown) -->
      <FileTree
        v-else
        :root-path="rootPath"
        :selected-files="selectedFileIds"
        @file-click="handleFileClick"
        class="flex-1 overflow-y-auto"
      />
    </div>

    <!-- Resize Handle 1: Between File Tree and Chat -->
    <div
      ref="resizeHandle1Ref"
      class="w-1 bg-transparent hover:bg-purple-500/50 cursor-col-resize transition-colors flex-shrink-0 relative z-10"
      @mousedown="(e) => startResize(1, e)"
    >
      <div class="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1"></div>
    </div>

    <!-- Middle Panel: Chat -->
    <div 
      ref="chatPanelRef"
      class="flex flex-col min-w-0"
      :style="{ width: `${chatPanelWidth}px` }"
    >
      <ProjectChat
        :project-id="projectId"
        :folder-path="rootPath"
        :open-files="openFiles"
        class="flex-1"
      />
    </div>

    <!-- Resize Handle 2: Between Chat and Viewer (only shown when viewer is open) -->
    <div
      v-if="openFiles.length > 0"
      ref="resizeHandle2Ref"
      class="w-1 bg-transparent hover:bg-purple-500/50 cursor-col-resize transition-colors flex-shrink-0 relative z-10"
      @mousedown="(e) => startResize(2, e)"
    >
      <div class="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1"></div>
    </div>

    <!-- Right Panel: Viewer (only shown when files are open) -->
    <div
      v-if="openFiles.length > 0"
      ref="viewerPanelRef"
      class="flex-shrink-0 border-l border-white/10 flex flex-col bg-[#0a0a0a]"
      :style="{ width: `${viewerPanelWidth}px` }"
    >
      <FileViewerTabs
        :files="openFiles"
        :active-file-id="activeFileId"
        @close="handleFileClosed"
        @select="activeFileId = $event"
        @update-model="handleModelUpdate"
        class="flex-1"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import FileTree from '~/components/FileTree.vue'
import ProjectChat from '~/components/ProjectChat.vue'
import FileViewerTabs from '~/components/FileViewerTabs.vue'
import ProjectStatistics from '~/components/ProjectStatistics.vue'

export interface OpenFile {
  id: string
  name: string
  path: string
  type: 'model' | 'pdf' | 'excel' | 'doc' | 'image' | 'other'
  streamId?: string
  models?: Array<{ id: string; name: string }>
  selectedModelId?: string
}

const props = defineProps<{
  projectId: string
  projectName: string
  rootPath: string
}>()

defineEmits<{
  back: []
}>()

const STORAGE_KEY = 'project-workspace-panel-widths'

// Panel width state
const leftPanelWidth = ref(288) // 72 * 4 = 288px (w-72)
const chatPanelWidth = ref(0) // Will be calculated
const viewerPanelWidth = ref(0) // Will be calculated

// Panel refs
const leftPanelRef = ref<HTMLElement | null>(null)
const chatPanelRef = ref<HTMLElement | null>(null)
const viewerPanelRef = ref<HTMLElement | null>(null)
const resizeHandle1Ref = ref<HTMLElement | null>(null)
const resizeHandle2Ref = ref<HTMLElement | null>(null)

// Resize state
const isResizing = ref(false)
const activeResizeHandle = ref<number | null>(null)
const resizeStartX = ref(0)
const resizeStartLeftWidth = ref(0)
const resizeStartChatWidth = ref(0)
const resizeStartViewerWidth = ref(0)

const openFiles = ref<OpenFile[]>([])
const activeFileId = ref<string | null>(null)
const showStatistics = ref(false)

const selectedFileIds = computed(() => new Set(openFiles.value.map(f => f.id)))

// Load saved widths from localStorage
function loadPanelWidths() {
  if (typeof window === 'undefined') return
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const widths = JSON.parse(stored)
      leftPanelWidth.value = widths.left || 288
      chatPanelWidth.value = widths.chat || 0
      viewerPanelWidth.value = widths.viewer || 0
    }
  } catch (error) {
    console.error('Error loading panel widths:', error)
  }
}

// Save widths to localStorage
function savePanelWidths() {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      left: leftPanelWidth.value,
      chat: chatPanelWidth.value,
      viewer: viewerPanelWidth.value
    }))
  } catch (error) {
    console.error('Error saving panel widths:', error)
  }
}

// Calculate chat and viewer widths based on available space
function calculatePanelWidths() {
  if (typeof window === 'undefined') return
  
  const totalWidth = window.innerWidth
  const availableWidth = totalWidth - leftPanelWidth.value - (openFiles.value.length > 0 ? viewerPanelWidth.value : 0)
  
  if (openFiles.value.length > 0) {
    // If viewer is open, split remaining space
    if (chatPanelWidth.value === 0 || viewerPanelWidth.value === 0) {
      // First time opening viewer, split 50/50
      const remaining = availableWidth
      chatPanelWidth.value = remaining / 2
      viewerPanelWidth.value = remaining / 2
    } else {
      // Maintain current proportions but adjust for available space
      const total = chatPanelWidth.value + viewerPanelWidth.value
      const chatRatio = chatPanelWidth.value / total
      const viewerRatio = viewerPanelWidth.value / total
      chatPanelWidth.value = availableWidth * chatRatio
      viewerPanelWidth.value = availableWidth * viewerRatio
    }
  } else {
    // No viewer, chat takes all remaining space
    chatPanelWidth.value = availableWidth
    viewerPanelWidth.value = 0
  }
}

function startResize(handleNumber: number, e: MouseEvent) {
  isResizing.value = true
  activeResizeHandle.value = handleNumber
  resizeStartX.value = e.clientX
  resizeStartLeftWidth.value = leftPanelWidth.value
  resizeStartChatWidth.value = chatPanelWidth.value
  resizeStartViewerWidth.value = viewerPanelWidth.value
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(e: MouseEvent) {
  if (!isResizing.value || activeResizeHandle.value === null) return
  
  const deltaX = e.clientX - resizeStartX.value
  
  if (activeResizeHandle.value === 1) {
    // Resizing between file tree and chat
    const newLeftWidth = Math.max(200, Math.min(600, resizeStartLeftWidth.value + deltaX))
    const newChatWidth = Math.max(300, resizeStartChatWidth.value - deltaX)
    
    if (newChatWidth >= 300) {
      leftPanelWidth.value = newLeftWidth
      chatPanelWidth.value = newChatWidth
    }
  } else if (activeResizeHandle.value === 2) {
    // Resizing between chat and viewer
    const newChatWidth = Math.max(300, resizeStartChatWidth.value + deltaX)
    const newViewerWidth = Math.max(300, resizeStartViewerWidth.value - deltaX)
    
    if (newViewerWidth >= 300) {
      chatPanelWidth.value = newChatWidth
      viewerPanelWidth.value = newViewerWidth
    }
  }
  
  savePanelWidths()
}

function stopResize() {
  isResizing.value = false
  activeResizeHandle.value = null
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function getFileType(fileName: string): OpenFile['type'] {
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  
  // Model files
  if (['rvt', 'ifc', 'dwg', 'dxf', 'skp', 'fbx', 'obj', '3dm'].includes(ext)) {
    return 'model'
  }
  
  // PDF files
  if (ext === 'pdf') {
    return 'pdf'
  }
  
  // Excel files
  if (['xlsx', 'xls', 'xlsm', 'csv'].includes(ext)) {
    return 'excel'
  }
  
  // Document files
  if (['doc', 'docx', 'txt', 'md'].includes(ext)) {
    return 'doc'
  }
  
  // Image files
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
    return 'image'
  }
  
  return 'other'
}

function handleFileClick(file: { name: string; path: string; streamId?: string; models?: Array<{ id: string; name: string }> }) {
  const fileId = file.path
  
  // Check if file is already open
  const existingIndex = openFiles.value.findIndex(f => f.id === fileId)
  
  if (existingIndex >= 0) {
    // File is already open, just activate it
    activeFileId.value = fileId
  } else {
    // Add new file to open files
    const newFile: OpenFile = {
      id: fileId,
      name: file.name,
      path: file.path,
      type: getFileType(file.name),
      streamId: file.streamId,
      models: file.models,
      selectedModelId: file.models && file.models.length > 0 ? file.models[0].id : undefined
    }
    openFiles.value.push(newFile)
    activeFileId.value = fileId
    
    // Recalculate panel widths when viewer opens
    if (openFiles.value.length === 1) {
      calculatePanelWidths()
    }
  }
}

function handleFileClosed(fileId: string) {
  const index = openFiles.value.findIndex(f => f.id === fileId)
  if (index >= 0) {
    openFiles.value.splice(index, 1)
    
    // If the closed file was active, activate another file
    if (activeFileId.value === fileId) {
      if (openFiles.value.length > 0) {
        // Activate the previous file, or the first one if we closed the first
        const newIndex = Math.min(index, openFiles.value.length - 1)
        activeFileId.value = openFiles.value[newIndex]?.id || null
      } else {
        activeFileId.value = null
        // Recalculate when viewer closes
        calculatePanelWidths()
      }
    }
  }
}

function handleModelUpdate(fileId: string, modelId: string) {
  const file = openFiles.value.find(f => f.id === fileId)
  if (file) {
    file.selectedModelId = modelId
  }
}

// Watch for window resize
function handleWindowResize() {
  calculatePanelWidths()
}

onMounted(() => {
  loadPanelWidths()
  calculatePanelWidths()
  window.addEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  stopResize()
})
</script>
