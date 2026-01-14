<template>
  <div>
    <!-- Node -->
    <div
      :class="[
        'flex items-center gap-1.5 px-2 py-1.5 mx-1 rounded-lg cursor-pointer transition group',
        isSelected ? 'bg-purple-600/20 text-white' : 'hover:bg-white/5 text-white/80 hover:text-white'
      ]"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
      @click="handleClick"
    >
      <!-- Expand/Collapse Arrow (for folders) -->
      <button
        v-if="item.is_directory"
        @click.stop="handleToggle"
        class="w-4 h-4 flex items-center justify-center text-white/40 hover:text-white/70 transition"
      >
        <svg 
          class="w-3 h-3 transition-transform" 
          :class="isExpanded ? 'rotate-90' : ''"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
      <div v-else class="w-4 h-4"></div>

      <!-- Icon -->
      <component :is="iconComponent" class="w-4 h-4 flex-shrink-0" :class="iconClass" />

      <!-- Name -->
      <span class="flex-1 truncate text-sm">{{ item.name }}</span>

      <!-- Status Indicator (for files only) -->
      <div v-if="!item.is_directory" class="flex items-center gap-2">
        <!-- Database Status Dot -->
        <div
          v-if="showStatusIndicator"
          :class="[
            'w-2 h-2 rounded-full flex-shrink-0',
            item.inDatabase ? 'bg-green-500' : 'bg-red-500'
          ]"
          :title="item.inDatabase ? 'File is in database' : 'File is not in database'"
        ></div>
        
        <!-- File size -->
        <span v-if="item.size_bytes" class="text-xs text-white/30 group-hover:text-white/50">
          {{ formatSize(item.size_bytes) }}
        </span>
      </div>
    </div>

    <!-- Children (for expanded folders) -->
    <div v-if="item.is_directory && isExpanded">
      <!-- Loading -->
      <div v-if="!item.childrenLoaded" class="flex items-center gap-2 px-2 py-1.5" :style="{ paddingLeft: `${(depth + 1) * 16 + 8}px` }">
        <div class="w-3 h-3 animate-spin rounded-full border border-purple-500 border-t-transparent"></div>
        <span class="text-xs text-white/40">Loading...</span>
      </div>
      
      <!-- Children -->
      <FileTreeNode
        v-else
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :selected-files="selectedFiles"
        :expanded-folders="expandedFolders"
        :depth="depth + 1"
        @file-click="$emit('file-click', $event)"
        @toggle-folder="$emit('toggle-folder', $event)"
        @load-children="$emit('load-children', $event)"
      />
      
      <!-- Empty folder -->
      <div 
        v-if="item.childrenLoaded && (!item.children || item.children.length === 0)" 
        class="text-xs text-white/30 px-2 py-1.5"
        :style="{ paddingLeft: `${(depth + 1) * 16 + 8}px` }"
      >
        Empty folder
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'

interface TreeItem {
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
  item: TreeItem
  selectedFiles: Set<string>
  expandedFolders: Set<string>
  depth: number
}>()

const emit = defineEmits<{
  'file-click': [file: { name: string; path: string; streamId?: string; models?: Array<{ id: string; name: string }> }]
  'toggle-folder': [path: string]
  'load-children': [path: string]
}>()

const isExpanded = computed(() => props.expandedFolders.has(props.item.path))
const isSelected = computed(() => props.selectedFiles.has(props.item.path))

// Show status indicator for .rvt files (or all files if inDatabase is set)
const showStatusIndicator = computed(() => {
  if (props.item.is_directory) return false
  // Show for .rvt files, or any file that has inDatabase property set
  const ext = props.item.name.split('.').pop()?.toLowerCase() || ''
  return ext === 'rvt' || props.item.inDatabase !== undefined
})

const fileExtension = computed(() => {
  if (props.item.is_directory) return ''
  return props.item.name.split('.').pop()?.toLowerCase() || ''
})

const iconComponent = computed(() => {
  // Return SVG component based on file type
  if (props.item.is_directory) {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })
    ])
  }
  
  const ext = fileExtension.value
  
  // Model files
  if (['rvt', 'ifc', 'dwg', 'dxf', 'skp', 'fbx', 'obj', '3dm'].includes(ext)) {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' })
    ])
  }
  
  // PDF files
  if (ext === 'pdf') {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z' })
    ])
  }
  
  // Excel files
  if (['xlsx', 'xls', 'xlsm', 'csv'].includes(ext)) {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' })
    ])
  }
  
  // Image files
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' })
    ])
  }
  
  // Default file icon
  return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
    h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' })
  ])
})

const iconClass = computed(() => {
  if (props.item.is_directory) {
    return isExpanded.value ? 'text-purple-400' : 'text-blue-400'
  }
  
  const ext = fileExtension.value
  
  if (['rvt', 'ifc', 'dwg', 'dxf', 'skp', 'fbx', 'obj', '3dm'].includes(ext)) {
    return 'text-green-400'
  }
  if (ext === 'pdf') {
    return 'text-red-400'
  }
  if (['xlsx', 'xls', 'xlsm', 'csv'].includes(ext)) {
    return 'text-emerald-400'
  }
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
    return 'text-blue-400'
  }
  
  return 'text-white/50'
})

function handleClick() {
  if (props.item.is_directory) {
    handleToggle()
  } else {
    emit('file-click', { 
      name: props.item.name, 
      path: props.item.path,
      streamId: props.item.streamId,
      models: props.item.models
    })
  }
}

function handleToggle() {
  emit('toggle-folder', props.item.path)
  
  // Load children if not already loaded
  if (!props.item.childrenLoaded && !isExpanded.value) {
    emit('load-children', props.item.path)
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
