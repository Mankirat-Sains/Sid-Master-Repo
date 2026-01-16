<template>
  <div class="h-full bg-[#0f0f0f] text-white overflow-hidden knowledge-base-view">
    <div class="h-full flex flex-col">
      <!-- Header -->
      <header class="border-b border-white/10 bg-[#0f0f0f] backdrop-blur-xl p-6">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-white/50">Agent Resources</p>
          <h1 class="text-2xl font-semibold text-white">Knowledge Base</h1>
          <p class="text-sm text-white/65 mt-1">
            View all files, directories, and tools the agent can access
          </p>
        </div>
      </header>

      <!-- Tabs -->
      <div class="border-b border-white/10 bg-[#0f0f0f] px-6">
        <div class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-4 py-3 text-sm font-medium transition-all duration-200',
              activeTab === tab.id
                ? 'text-white border-b-2 border-purple-500'
                : 'text-white/60 hover:text-white/80'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Tab 1: In Memory -->
        <div v-if="activeTab === 'memory'" class="space-y-6">
          <!-- Auto-imported/System Files -->
          <section class="card">
            <div class="mb-4">
              <h2 class="text-lg font-semibold text-white">System Files</h2>
              <p class="text-xs text-white/60">Files automatically imported by the agent</p>
            </div>
            
            <!-- Filters for System Files -->
            <div class="mb-4 p-4 bg-white/5 rounded-lg border border-white/10">
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Project Name</label>
                  <input
                    v-model="systemFilters.project"
                    type="text"
                    placeholder="Type to filter..."
                    class="input text-sm"
                  />
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">File Type</label>
                  <select v-model="systemFilters.fileType" class="input text-sm">
                    <option value="">All Types</option>
                    <option v-for="type in uniqueFileTypes" :key="type" :value="type">{{ type }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Date Uploaded</label>
                  <input
                    v-model="systemFilters.dateUploaded"
                    type="date"
                    class="input text-sm"
                  />
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Who Uploaded</label>
                  <select v-model="systemFilters.whoUploaded" class="input text-sm">
                    <option value="">All Users</option>
                    <option v-for="user in sortedUsers" :key="user" :value="user">{{ user }}</option>
                  </select>
                </div>
              </div>
              <div class="mt-3 flex justify-end">
                <button class="btn-secondary text-xs" @click="clearSystemFilters">Clear Filters</button>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-white/10">
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">File Name</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Project</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">File Type</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Date Uploaded</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Who Uploaded</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Description</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Link</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="file in filteredSystemFiles"
                    :key="file.id"
                    class="border-b border-white/5 hover:bg-white/5 transition"
                  >
                    <td class="py-3 px-4 text-sm text-white">{{ file.fileName }}</td>
                    <td class="py-3 px-4 text-sm text-white/80">{{ file.project }}</td>
                    <td class="py-3 px-4">
                      <span class="pill">{{ file.fileType }}</span>
                    </td>
                    <td class="py-3 px-4 text-sm text-white/80">{{ file.dateUploaded }}</td>
                    <td class="py-3 px-4 text-sm text-white/80">{{ file.whoUploaded }}</td>
                    <td class="py-3 px-4 text-sm text-white/70">{{ file.description }}</td>
                    <td class="py-3 px-4">
                      <a :href="file.link" class="text-purple-400 hover:text-purple-300 text-sm">View</a>
                    </td>
                  </tr>
                  <tr v-if="filteredSystemFiles.length === 0">
                    <td colspan="7" class="py-8 text-center text-white/60 text-sm">No files match the current filters</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- User-uploaded Files -->
          <section class="card">
            <div class="mb-4 flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold text-white">User-Uploaded Files</h2>
                <p class="text-xs text-white/60">Files manually uploaded with modification history</p>
              </div>
              <div v-if="hasUserFilters" class="text-xs text-white/60">
                Showing {{ filteredGroupedUserFiles.length }} of {{ groupedUserFiles.length }} files
              </div>
            </div>
            
            <!-- Filters for User Files -->
            <div class="mb-4 p-4 bg-white/5 rounded-lg border border-white/10">
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Directory</label>
                  <input
                    v-model="userFilters.directory"
                    type="text"
                    placeholder="Type to filter..."
                    class="input text-sm"
                  />
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Date Uploaded</label>
                  <input
                    v-model="userFilters.dateUploaded"
                    type="date"
                    class="input text-sm"
                  />
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Who Uploaded</label>
                  <select v-model="userFilters.whoUploaded" class="input text-sm">
                    <option value="">All Users</option>
                    <option v-for="user in sortedUsers" :key="user" :value="user">{{ user }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-white/70 mb-1.5">Description</label>
                  <input
                    v-model="userFilters.description"
                    type="text"
                    placeholder="Type to filter..."
                    class="input text-sm"
                  />
                </div>
              </div>
              <div class="mt-3 flex justify-end">
                <button class="btn-secondary text-xs" @click="clearUserFilters">Clear Filters</button>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-white/10">
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">File Name</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Directory</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Date Uploaded</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Who Uploaded</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider">Description</th>
                    <th class="text-left py-3 px-4 text-xs font-medium text-white/70 uppercase tracking-wider"># Modifications</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="file in filteredGroupedUserFiles"
                    :key="file.fileName"
                    class="border-b border-white/5 hover:bg-white/5 transition"
                  >
                    <td class="py-3 px-4 text-sm text-white">{{ file.fileName }}</td>
                    <td class="py-3 px-4 text-sm text-white/80 font-mono text-xs">{{ file.directory }}</td>
                    <td class="py-3 px-4 text-sm text-white/80">{{ file.dateUploaded }}</td>
                    <td class="py-3 px-4 text-sm text-white/80">{{ file.whoUploaded }}</td>
                    <td class="py-3 px-4 text-sm text-white/70">{{ file.latestDescription }}</td>
                    <td class="py-3 px-4">
                      <div class="relative modification-dropdown-container">
                        <button
                          @click.stop="toggleModificationHistory(file.fileName)"
                          class="badge badge-info cursor-pointer hover:opacity-80 transition"
                        >
                          {{ file.modifications.length }}
                        </button>
                        <!-- Modification History Dropdown -->
                        <div
                          v-if="openModificationHistory === file.fileName"
                          class="absolute right-0 top-full mt-2 z-50 min-w-[400px] max-w-[500px] bg-[#1a1a1a] border border-white/20 rounded-lg shadow-2xl p-4"
                          @click.stop
                        >
                          <div class="flex items-center justify-between mb-3">
                            <h4 class="text-sm font-semibold text-white">Modification History</h4>
                            <button
                              @click="openModificationHistory = null"
                              class="text-white/60 hover:text-white text-sm"
                            >
                              ×
                            </button>
                          </div>
                          <div class="space-y-3 max-h-96 overflow-y-auto">
                            <div
                              v-for="(mod, idx) in file.modifications"
                              :key="idx"
                              class="p-3 bg-white/5 rounded-lg border border-white/10"
                            >
                              <div class="flex items-center justify-between mb-2">
                                <span class="text-xs font-semibold text-purple-400">Modification {{ mod.modificationNumber }}</span>
                                <span class="text-xs text-white/60">{{ formatDate(mod.dateUploaded) }}</span>
                              </div>
                              <div class="text-xs text-white/80 mb-1">
                                <span class="text-white/60">By:</span> {{ mod.whoUploaded }}
                              </div>
                              <div class="text-xs text-white/70 mt-2">
                                {{ mod.description }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="filteredGroupedUserFiles.length === 0">
                    <td colspan="6" class="py-8 text-center text-white/60 text-sm">No files match the current filters</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <!-- Tab 2: Local Access -->
        <div v-if="activeTab === 'local'" class="space-y-6">
          <section class="card">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h2 class="text-lg font-semibold text-white">Local Directories</h2>
                <p class="text-xs text-white/60">Directories the local agent can access</p>
              </div>
              <button class="btn-primary" @click="showAddDirectory = true">
                Add Directory
              </button>
            </div>
            <div class="space-y-2">
              <div
                v-for="dir in localDirectories"
                :key="dir.path"
                class="card-row flex items-center justify-between"
              >
                <div class="flex-1">
                  <p class="text-sm font-medium text-white font-mono">{{ dir.path }}</p>
                  <p class="text-xs text-white/60 mt-1">Added {{ dir.dateAdded }} by {{ dir.addedBy }}</p>
                </div>
                <button 
                  class="text-red-400 hover:text-red-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed transition" 
                  @click.stop="removeDirectory(dir.path)"
                  :disabled="isRemovingDirectory === dir.path"
                >
                  {{ isRemovingDirectory === dir.path ? 'Removing...' : 'Remove' }}
                </button>
              </div>
              <div v-if="!isLoadingDirectories && localDirectories.length === 0" class="text-center py-8 text-white/60">
                No directories configured. Add a directory to allow local agent access.
              </div>
            </div>
          </section>

          <!-- Add Directory Modal (simple placeholder) -->
          <div v-if="showAddDirectory" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div class="card max-w-md w-full mx-4">
              <h3 class="text-lg font-semibold text-white mb-4">Add Directory</h3>
              <input
                v-model="newDirectoryPath"
                type="text"
                placeholder="/path/to/directory"
                class="input mb-4"
                @keyup.enter="addDirectory"
                :disabled="isAddingDirectory"
              />
              <div v-if="directoryError" class="mb-3 p-2 bg-red-500/20 border border-red-500/50 rounded text-xs text-red-400">
                {{ directoryError }}
              </div>
              <div class="flex gap-3 justify-end">
                <button 
                  class="btn-secondary" 
                  @click="showAddDirectory = false; directoryError = null; newDirectoryPath = ''"
                  :disabled="isAddingDirectory"
                >
                  Cancel
                </button>
                <button 
                  class="btn-primary" 
                  @click="addDirectory"
                  :disabled="isAddingDirectory || !newDirectoryPath.trim()"
                >
                  {{ isAddingDirectory ? 'Adding...' : 'Add' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: Tools & Services -->
        <div v-if="activeTab === 'tools'" class="space-y-6">
          <section class="card">
            <div class="mb-4">
              <h2 class="text-lg font-semibold text-white">Available Tools & Services</h2>
              <p class="text-xs text-white/60">External tools and services the agent can access</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="tool in tools"
                :key="tool.id"
                class="card-row"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="text-base font-semibold text-white">{{ tool.name }}</h3>
                    <p class="text-xs text-white/60 mt-1">{{ tool.description }}</p>
                    <div class="mt-3 space-y-1">
                      <div class="flex items-center gap-2">
                        <span class="text-xs text-white/50">Status:</span>
                        <span
                          :class="[
                            'badge',
                            tool.licensed ? 'badge-success' : 'badge-muted'
                          ]"
                        >
                          {{ tool.licensed ? 'Licensed' : 'Available' }}
                        </span>
                      </div>
                      <div v-if="tool.licensed" class="text-xs text-white/60">
                        <span class="text-white/50">License Key:</span>
                        <span class="font-mono ml-2">{{ tool.licenseKey }}</span>
                      </div>
                      <div v-if="tool.licensed" class="text-xs text-white/60">
                        <span class="text-white/50">Expires:</span>
                        <span class="ml-2">{{ tool.licenseExpiry }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

// Tab configuration
const tabs = [
  { id: 'memory', label: 'In Memory' },
  { id: 'local', label: 'Local Access' },
  { id: 'tools', label: 'Tools & Services' }
]

const activeTab = ref('memory')

// Tab 1: System Files (Auto-imported)
interface SystemFile {
  id: string
  fileName: string
  project: string
  fileType: string
  dateUploaded: string
  whoUploaded: string
  description: string
  link: string
}

const systemFiles = ref<SystemFile[]>([
  {
    id: '1',
    fileName: 'beam.xlsx',
    project: '25-01-050 Martin Gate Bridge',
    fileType: 'Excel',
    dateUploaded: '2026-01-10',
    whoUploaded: 'System',
    description: 'Beam design template',
    link: '#'
  },
  {
    id: '2',
    fileName: 'column_calcs.pdf',
    project: '25-01-050 Martin Gate Bridge',
    fileType: 'PDF',
    dateUploaded: '2026-01-11',
    whoUploaded: 'System',
    description: 'Column calculations',
    link: '#'
  },
  {
    id: '3',
    fileName: 'foundation_design.xlsx',
    project: '25-01-051 Office Building',
    fileType: 'Excel',
    dateUploaded: '2026-01-12',
    whoUploaded: 'Sarah',
    description: 'Foundation calculations',
    link: '#'
  },
  {
    id: '4',
    fileName: 'structural_analysis.pdf',
    project: '25-01-050 Martin Gate Bridge',
    fileType: 'PDF',
    dateUploaded: '2026-01-13',
    whoUploaded: 'Mike',
    description: 'Structural analysis report',
    link: '#'
  }
])

// System Files Filters
const systemFilters = ref({
  project: '',
  fileType: '',
  dateUploaded: '',
  whoUploaded: ''
})

// Tab 1: User-uploaded Files with Modification History
interface FileModification {
  modificationNumber: number
  dateUploaded: string
  whoUploaded: string
  description: string
}

interface UserFileWithHistory {
  id: string
  fileName: string
  directory: string
  dateUploaded: string
  whoUploaded: string
  description: string
  modifications: FileModification[]
}

const userFilesWithHistory = ref<UserFileWithHistory[]>([
  {
    id: '1',
    fileName: 'Beam.xlsx',
    directory: 'XX/XX/XXX',
    dateUploaded: '2026-01-13',
    whoUploaded: 'James',
    description: 'Starting a Design',
    modifications: [
      {
        modificationNumber: 1,
        dateUploaded: '2026-01-13',
        whoUploaded: 'James',
        description: 'Starting a Design'
      },
      {
        modificationNumber: 2,
        dateUploaded: '2026-01-15',
        whoUploaded: 'James',
        description: 'loading updated because arch changed'
      },
      {
        modificationNumber: 3,
        dateUploaded: '2026-01-18',
        whoUploaded: 'James',
        description: 'Updated beam sizes based on new loading requirements'
      }
    ]
  },
  {
    id: '2',
    fileName: 'Column_Design.xlsx',
    directory: 'YY/YY/YYY',
    dateUploaded: '2026-01-10',
    whoUploaded: 'Sarah',
    description: 'Initial column design',
    modifications: [
      {
        modificationNumber: 1,
        dateUploaded: '2026-01-10',
        whoUploaded: 'Sarah',
        description: 'Initial column design'
      },
      {
        modificationNumber: 2,
        dateUploaded: '2026-01-12',
        whoUploaded: 'Sarah',
        description: 'Adjusted column sizes for increased loads'
      }
    ]
  },
  {
    id: '3',
    fileName: 'Foundation_Calc.xlsx',
    directory: 'ZZ/ZZ/ZZZ',
    dateUploaded: '2026-01-08',
    whoUploaded: 'Mike',
    description: 'Foundation calculations',
    modifications: [
      {
        modificationNumber: 1,
        dateUploaded: '2026-01-08',
        whoUploaded: 'Mike',
        description: 'Foundation calculations'
      }
    ]
  }
])

// User Files Filters
const userFilters = ref({
  directory: '',
  dateUploaded: '',
  whoUploaded: '',
  description: ''
})

// Modification History Dropdown
const openModificationHistory = ref<string | null>(null)

function toggleModificationHistory(fileName: string) {
  if (openModificationHistory.value === fileName) {
    openModificationHistory.value = null
  } else {
    openModificationHistory.value = fileName
  }
}

// Close dropdown when clicking outside
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.modification-dropdown-container')) {
    openModificationHistory.value = null
  }
}

// Computed: Get unique file types from system files
const uniqueFileTypes = computed(() => {
  const types = new Set(systemFiles.value.map(f => f.fileType))
  return Array.from(types).sort()
})

// Computed: Get all unique users (sorted alphabetically)
const allUsers = computed(() => {
  const systemUsers = systemFiles.value.map(f => f.whoUploaded)
  const userUsers = userFilesWithHistory.value.map(f => f.whoUploaded)
  const allModUsers = userFilesWithHistory.value.flatMap(f => 
    f.modifications.map(m => m.whoUploaded)
  )
  const uniqueUsers = new Set([...systemUsers, ...userUsers, ...allModUsers])
  return Array.from(uniqueUsers).sort()
})

const sortedUsers = computed(() => allUsers.value)

// Computed: Check if system filters are active
const hasSystemFilters = computed(() => {
  return !!(
    systemFilters.value.project ||
    systemFilters.value.fileType ||
    systemFilters.value.dateUploaded ||
    systemFilters.value.whoUploaded
  )
})

// Computed: Filtered System Files
const filteredSystemFiles = computed(() => {
  return systemFiles.value.filter(file => {
    if (systemFilters.value.project && !file.project.toLowerCase().includes(systemFilters.value.project.toLowerCase())) {
      return false
    }
    if (systemFilters.value.fileType && file.fileType !== systemFilters.value.fileType) {
      return false
    }
    if (systemFilters.value.dateUploaded) {
      // Compare dates (YYYY-MM-DD format)
      const fileDate = file.dateUploaded.split('T')[0] // Handle ISO dates
      if (fileDate !== systemFilters.value.dateUploaded) {
        return false
      }
    }
    if (systemFilters.value.whoUploaded && file.whoUploaded !== systemFilters.value.whoUploaded) {
      return false
    }
    return true
  })
})

// Computed: Group User Files by filename (only show one instance)
interface GroupedUserFile {
  fileName: string
  directory: string
  dateUploaded: string
  whoUploaded: string
  latestDescription: string
  modifications: FileModification[]
}

const groupedUserFiles = computed(() => {
  const grouped = new Map<string, GroupedUserFile>()
  
  userFilesWithHistory.value.forEach(file => {
    if (!grouped.has(file.fileName)) {
      grouped.set(file.fileName, {
        fileName: file.fileName,
        directory: file.directory,
        dateUploaded: file.dateUploaded,
        whoUploaded: file.whoUploaded,
        latestDescription: file.description,
        modifications: [...file.modifications]
      })
    } else {
      // Merge modifications if same filename
      const existing = grouped.get(file.fileName)!
      existing.modifications.push(...file.modifications)
      existing.modifications.sort((a, b) => 
        new Date(a.dateUploaded).getTime() - new Date(b.dateUploaded).getTime()
      )
      // Update to latest description
      if (new Date(file.dateUploaded) > new Date(existing.dateUploaded)) {
        existing.latestDescription = file.description
        existing.dateUploaded = file.dateUploaded
      }
    }
  })
  
  return Array.from(grouped.values())
})

// Computed: Check if user filters are active
const hasUserFilters = computed(() => {
  return !!(
    userFilters.value.directory ||
    userFilters.value.dateUploaded ||
    userFilters.value.whoUploaded ||
    userFilters.value.description
  )
})

// Computed: Filtered Grouped User Files
const filteredGroupedUserFiles = computed(() => {
  return groupedUserFiles.value.filter(file => {
    if (userFilters.value.directory && !file.directory.toLowerCase().includes(userFilters.value.directory.toLowerCase())) {
      return false
    }
    if (userFilters.value.dateUploaded) {
      // Compare dates (YYYY-MM-DD format)
      const fileDate = file.dateUploaded.split('T')[0] // Handle ISO dates
      if (fileDate !== userFilters.value.dateUploaded) {
        return false
      }
    }
    if (userFilters.value.whoUploaded && file.whoUploaded !== userFilters.value.whoUploaded) {
      return false
    }
    if (userFilters.value.description && !file.latestDescription.toLowerCase().includes(userFilters.value.description.toLowerCase())) {
      return false
    }
    return true
  })
})

function clearSystemFilters() {
  systemFilters.value = {
    project: '',
    fileType: '',
    dateUploaded: '',
    whoUploaded: ''
  }
}

function clearUserFilters() {
  userFilters.value = {
    directory: '',
    dateUploaded: '',
    whoUploaded: '',
    description: ''
  }
}

// Format date for display
function formatDate(dateString: string): string {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateString
  }
}

// Tab 2: Local Directories
interface LocalDirectory {
  path: string
  dateAdded: string
  addedBy: string
}

const localDirectories = ref<LocalDirectory[]>([])
const isLoadingDirectories = ref(false)
const directoryError = ref<string | null>(null)

// API base URL for local agent
const AGENT_API_URL = 'http://localhost:8001'

const showAddDirectory = ref(false)
const newDirectoryPath = ref('')
const isAddingDirectory = ref(false)
const isRemovingDirectory = ref<string | null>(null)

// Fetch directories from API
async function fetchDirectories() {
  isLoadingDirectories.value = true
  directoryError.value = null
  
  try {
    const response = await $fetch<LocalDirectory[]>(`${AGENT_API_URL}/api/agent/directories`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    localDirectories.value = response.map(dir => ({
      path: dir.path,
      dateAdded: formatDate(dir.dateAdded),
      addedBy: dir.addedBy
    }))
  } catch (error: any) {
    console.error('Error fetching directories:', error)
    directoryError.value = error.data?.detail || error.message || 'Failed to fetch directories'
    localDirectories.value = []
  } finally {
    isLoadingDirectories.value = false
  }
}

async function addDirectory() {
  const trimmedPath = newDirectoryPath.value.trim()
  
  if (!trimmedPath) {
    directoryError.value = 'Please enter a directory path'
    return
  }
  
  isAddingDirectory.value = true
  directoryError.value = null
  
  try {
    const response = await $fetch<LocalDirectory>(`${AGENT_API_URL}/api/agent/directories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        path: trimmedPath,
        addedBy: 'User'
      }
    })
    
    // Refresh directories list
    await fetchDirectories()
    
    newDirectoryPath.value = ''
    showAddDirectory.value = false
    directoryError.value = null
  } catch (error: any) {
    console.error('Error adding directory:', error)
    // Parse error message more clearly
    if (error.data?.detail) {
      directoryError.value = error.data.detail
    } else if (error.data && Array.isArray(error.data)) {
      // Handle validation errors
      const validationErrors = error.data.map((e: any) => e.msg || e.message).join(', ')
      directoryError.value = validationErrors
    } else {
      directoryError.value = error.message || 'Failed to add directory'
    }
  } finally {
    isAddingDirectory.value = false
  }
}

async function removeDirectory(path: string) {
  if (isRemovingDirectory.value === path) return
  
  isRemovingDirectory.value = path
  directoryError.value = null
  
  try {
    await $fetch(`${AGENT_API_URL}/api/agent/directories`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        path: path
      }
    })
    
    // Refresh directories list
    await fetchDirectories()
  } catch (error: any) {
    console.error('Error removing directory:', error)
    directoryError.value = error.data?.detail || error.message || 'Failed to remove directory'
  } finally {
    isRemovingDirectory.value = null
  }
}

// Fetch directories when component mounts and when Local Access tab is opened
onMounted(() => {
  // Fetch when Local Access tab is first opened
  if (activeTab.value === 'local') {
    fetchDirectories()
  }
})

// Watch for tab changes to fetch directories
watch(activeTab, (newTab) => {
  if (newTab === 'local' && localDirectories.value.length === 0 && !isLoadingDirectories.value) {
    fetchDirectories()
  }
})

// Tab 3: Tools & Services
interface Tool {
  id: string
  name: string
  description: string
  licensed: boolean
  licenseKey?: string
  licenseExpiry?: string
}

const tools = ref<Tool[]>([
  {
    id: '1',
    name: 'Revit',
    description: 'Autodesk Revit integration for BIM models',
    licensed: true,
    licenseKey: 'XXXX-XXXX-XXXX-XXXX',
    licenseExpiry: '2026-Dec-31'
  },
  {
    id: '2',
    name: 'ETABS',
    description: 'Structural analysis and design',
    licensed: true,
    licenseKey: 'YYYY-YYYY-YYYY-YYYY',
    licenseExpiry: '2026-Jun-30'
  },
  {
    id: '3',
    name: 'SAP2000',
    description: 'General structural analysis',
    licensed: true,
    licenseKey: 'ZZZZ-ZZZZ-ZZZZ-ZZZZ',
    licenseExpiry: '2026-Dec-31'
  },
  {
    id: '4',
    name: 'Web Search',
    description: 'Internet search capabilities',
    licensed: false
  },
  {
    id: '5',
    name: 'Gmail',
    description: 'Email integration',
    licensed: false
  },
  {
    id: '6',
    name: 'RISA',
    description: 'Structural engineering software',
    licensed: true,
    licenseKey: 'AAAA-BBBB-CCCC-DDDD',
    licenseExpiry: '2027-Jan-15'
  }
])
</script>

<style scoped>
.knowledge-base-view {
  background: #0f0f0f;
  color: #fff;
}

.card {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.card-row {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.pill {
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(124, 58, 237, 0.15);
  color: #c084fc;
  border: 1px solid rgba(124, 58, 237, 0.25);
  font-size: 11px;
  font-weight: 600;
}

.badge {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 11px;
  text-transform: capitalize;
}

.badge-success {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.3);
}

.badge-info {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.3);
}

.badge-muted {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}

.btn-primary {
  background: rgba(124, 58, 237, 0.25);
  border: 1px solid rgba(124, 58, 237, 0.4);
  color: #e9d5ff;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  cursor: pointer;
}

.btn-primary:hover {
  background: rgba(124, 58, 237, 0.35);
  border-color: rgba(124, 58, 237, 0.5);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  cursor: pointer;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.input {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
  color: #fff;
  font-size: 14px;
}

.input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.input:focus {
  outline: none;
  border-color: rgba(124, 58, 237, 0.6);
  background: rgba(255, 255, 255, 0.06);
}

table {
  border-collapse: collapse;
}

table th {
  text-align: left;
  font-weight: 600;
}

select.input {
  cursor: pointer;
}

.custom-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.custom-scroll::-webkit-scrollbar {
  width: 6px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
