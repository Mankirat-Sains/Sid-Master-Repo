<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
    <div class="w-full max-w-4xl bg-[#111] border border-white/10 rounded-2xl shadow-2xl flex flex-col" style="height: 80vh;">
      <!-- Header -->
      <div class="flex-shrink-0 px-6 py-4 border-b border-white/10 flex items-center justify-between">
        <h2 class="text-xl font-semibold text-white">Select Folder</h2>
        <button
          @click="$emit('close')"
          class="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition flex items-center justify-center"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Folder Browser -->
      <div class="flex-1 min-h-0 overflow-hidden">
        <FolderBrowser
          :initial-path="initialPath"
          @path-change="currentPath = $event"
          @folder-selected="selectedPath = $event"
        />
      </div>

      <!-- Footer -->
      <div class="flex-shrink-0 px-6 py-4 border-t border-white/10 flex items-center justify-between">
        <div class="flex-1 min-w-0 mr-4">
          <p class="text-sm text-white/60 truncate" :title="selectedPath || currentPath">
            Selected: {{ selectedPath || currentPath || 'No folder selected' }}
          </p>
        </div>
        <div class="flex gap-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white transition"
          >
            Cancel
          </button>
          <button
            @click="confirmSelection"
            :disabled="!currentPath"
            class="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white transition"
          >
            Select This Folder
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FolderBrowser from '~/components/FolderBrowser.vue'

const emit = defineEmits<{
  close: []
  select: [path: string, name: string]
}>()

// Start from common locations - adjust based on OS
const initialPath = ref('/Volumes')
const currentPath = ref<string>('')
const selectedPath = ref<string>('')

function confirmSelection() {
  const pathToUse = selectedPath.value || currentPath.value
  if (!pathToUse) return
  
  // Extract folder name from path
  const folderName = pathToUse.split('/').filter(p => p).pop() || pathToUse
  
  emit('select', pathToUse, folderName)
}
</script>
