<template>
  <div class="h-full w-full flex flex-col bg-[#0f0f0f] text-white overflow-hidden">
    <!-- Header -->
    <div class="flex-shrink-0 px-6 py-4 border-b border-white/10 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button
          @click="$emit('close')"
          class="p-2 rounded-lg hover:bg-white/10 transition"
          aria-label="Close"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div>
          <h2 class="text-lg font-semibold text-white">Live Calculations</h2>
          <p class="text-xs text-white/60">Real-time Excel data sync</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="forceSync"
          :disabled="isSyncing"
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ isSyncing ? 'Syncing...' : 'Sync' }}
        </button>
      </div>
    </div>

    <!-- Agent Status Bar -->
    <div class="flex-shrink-0 px-6 py-3 bg-white/5 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-2 h-2 rounded-full',
            agentStatus?.status === 'idle' || agentStatus?.status === 'stopped' ? 'bg-green-500' :
            agentStatus?.status === 'syncing' ? 'bg-yellow-500 animate-pulse' :
            'bg-red-500'
          ]"
        ></div>
        <span class="text-sm text-white/80">
          {{ agentStatus?.agent_configured ? 'Agent Connected' : 'Agent Not Configured' }}
        </span>
        <span v-if="selectedProject" class="text-sm text-white/60">
          - {{ selectedProject.project_name }}
        </span>
        <span v-if="lastSyncTime" class="ml-auto text-xs text-white/50">
          Last sync: {{ lastSyncTime }}
        </span>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 min-h-0 overflow-y-auto">
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-center space-y-4">
          <div class="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p class="text-white/60">Loading project data...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-6">
        <div class="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
          <p class="text-red-300">{{ error }}</p>
          <button
            @click="loadData"
            class="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- No Projects State -->
      <div v-else-if="projects.length === 0" class="flex items-center justify-center h-full">
        <div class="text-center space-y-4 max-w-md">
          <svg class="w-16 h-16 mx-auto text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-white/60">No projects configured</p>
          <p class="text-sm text-white/40">Configure the Excel Sync Agent to get started</p>
        </div>
      </div>

      <!-- Project Data Display -->
      <div v-else class="p-6 space-y-6">
        <!-- Project Selector (if multiple) -->
        <div v-if="projects.length > 1" class="mb-4">
          <label class="block text-sm font-medium text-white/70 mb-2">Select Project</label>
          <select
            v-model="selectedProjectId"
            class="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
              {{ project.project_name }}
            </option>
          </select>
        </div>

        <!-- Project Data -->
        <div v-if="projectData" class="space-y-6">
          <!-- Project Type Section -->
          <div class="bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 class="text-lg font-semibold text-white mb-4">Project Type</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="(value, key) in projectData.data"
                :key="key"
                class="flex items-center justify-between py-2 border-b border-white/10 last:border-b-0"
              >
                <span class="text-white/70 text-sm capitalize">{{ formatKey(key) }}:</span>
                <span class="text-white font-medium">{{ formatValue(value) }}</span>
              </div>
            </div>
          </div>

          <!-- Climatic Data Section -->
          <div class="bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 class="text-lg font-semibold text-white mb-2">Climatic Data</h3>
            <p class="text-sm text-white/60 mb-4">NBCC climatic loads for location</p>
            <div class="space-y-3">
              <div class="flex items-center justify-between py-2">
                <span class="text-white/70">Location:</span>
                <span class="text-white font-medium">{{ projectData.data.location || 'N/A' }}</span>
              </div>
              <div class="flex items-center justify-between py-2">
                <span class="text-white/70">Ground Snow Ss:</span>
                <span class="text-white font-medium">{{ formatValue(projectData.data.ground_snow_load) }} kPa</span>
              </div>
              <div class="flex items-center justify-between py-2">
                <span class="text-white/70">Ground Rain Sr:</span>
                <span class="text-white font-medium">{{ formatValue(projectData.data.ground_rain_load) }} kPa</span>
              </div>
              <div class="flex items-center justify-between py-2">
                <span class="text-white/70">Wind Load:</span>
                <span class="text-white font-medium">{{ formatValue(projectData.data.wind_load) }} kPa</span>
              </div>
              <div class="flex items-center justify-between py-2">
                <span class="text-white/70">Roof Pitch:</span>
                <span class="text-white font-medium">{{ formatRoofPitch(projectData.data.roof_pitch) }}</span>
              </div>
            </div>
          </div>

          <!-- All Data (Expandable) -->
          <div class="bg-white/5 border border-white/10 rounded-xl p-6">
            <details class="cursor-pointer">
              <summary class="text-sm font-medium text-white/80 hover:text-white transition">
                View All Data
              </summary>
              <div class="mt-4 space-y-2">
                <div
                  v-for="(value, key) in projectData.data"
                  :key="key"
                  class="flex items-center justify-between py-2 px-3 bg-white/5 rounded"
                >
                  <span class="text-white/70 text-sm font-mono">{{ key }}:</span>
                  <span class="text-white text-sm">{{ formatValue(value) }}</span>
                </div>
              </div>
            </details>
          </div>
        </div>

        <!-- No Data State -->
        <div v-else-if="selectedProjectId" class="text-center py-12">
          <p class="text-white/60">No data available for this project</p>
          <button
            @click="loadProjectData"
            class="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm"
          >
            Load Data
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useSyncAgent } from '~/composables/useSyncAgent'

const emit = defineEmits<{
  close: []
}>()

const { getStatus, getProjects, getProjectData, triggerSync } = useSyncAgent()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const agentStatus = ref<any>(null)
const projects = ref<any[]>([])
const selectedProjectId = ref<string | null>(null)
const projectData = ref<any>(null)
const isSyncing = ref(false)

// Computed
const selectedProject = computed(() => {
  return projects.value.find(p => p.project_id === selectedProjectId.value) || projects.value[0]
})

const lastSyncTime = computed(() => {
  if (!agentStatus.value?.last_sync) return null
  const date = new Date(agentStatus.value.last_sync)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleDateString()
})

// Methods
async function loadData() {
  loading.value = true
  error.value = null
  
  try {
    // Load agent status
    agentStatus.value = await getStatus()
    
    // Load projects
    projects.value = await getProjects()
    
    // Auto-select first project
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].project_id
    }
    
    // Load project data if project selected
    if (selectedProjectId.value) {
      await loadProjectData()
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load data'
    console.error('Load error:', err)
  } finally {
    loading.value = false
  }
}

async function loadProjectData() {
  if (!selectedProjectId.value) return
  
  try {
    projectData.value = await getProjectData(selectedProjectId.value)
  } catch (err: any) {
    console.error('Failed to load project data:', err)
    projectData.value = null
  }
}

async function forceSync() {
  if (isSyncing.value) return
  
  isSyncing.value = true
  try {
    await triggerSync(selectedProjectId.value || undefined)
    // Reload data after sync
    await loadProjectData()
    await loadData() // Refresh status
  } catch (err: any) {
    error.value = err.message || 'Sync failed'
  } finally {
    isSyncing.value = false
  }
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatValue(value: any): string {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'number') return value.toFixed(2)
  return String(value)
}

function formatRoofPitch(value: any): string {
  if (!value) return 'N/A'
  // Convert to "X in 12" format if needed
  const pitch = typeof value === 'number' ? value : parseFloat(value)
  if (isNaN(pitch)) return String(value)
  const degrees = (Math.atan(pitch / 12) * 180 / Math.PI).toFixed(1)
  return `${pitch} in 12 (${degrees} deg)`
}

// Watch for project changes
watch(selectedProjectId, () => {
  loadProjectData()
})

// Auto-refresh every 30 seconds
let refreshInterval: NodeJS.Timeout | null = null

onMounted(() => {
  loadData()
  refreshInterval = setInterval(() => {
    loadData()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
/* Custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
