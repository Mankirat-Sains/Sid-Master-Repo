<template>
  <div class="h-full work-view bg-[#0f0f0f] text-white overflow-hidden">
    <!-- Project Workspace View (for folder-based projects) -->
    <ProjectWorkspaceView
      v-if="selectedProject && selectedProject.localPath"
      :project-id="selectedProject.id"
      :project-name="selectedProject.name"
      :root-path="selectedProject.localPath"
      @back="clearSelection"
    />

    <!-- Workspace Content (shown when workspace has content - takes priority) -->
    <div v-else-if="workspaceState.mode !== 'empty'" class="h-full flex flex-col overflow-y-auto">
      <div class="flex-1 min-h-0 card-pane overflow-hidden">
        <!-- PDF Viewer -->
        <PDFViewer
          v-if="workspaceState.mode === 'pdf'"
          :pdf-url="workspaceState.pdfUrl"
          :file-url="workspaceState.pdfUrl"
          :file-name="workspaceState.pdfFileName"
          @close="workspace.clear()"
        />

        <!-- Draft Editor -->
        <DraftEditor
          v-else-if="workspaceState.mode === 'draft'"
          :title="workspaceState.draftTitle"
          :initial-content="workspaceState.draftContent"
          :loading="draftLoading"
          :loading-message="draftLoadingMessage"
          @update:content="workspace.updateDraftContent"
          @export-word="handleExportToWord"
          @close="workspace.clear()"
        />

        <!-- Model Viewer -->
        <SpeckleViewer
          v-else-if="workspaceState.mode === 'model'"
          :model-url="workspaceState.modelUrl"
          :model-name="workspaceState.modelName || 'Model'"
          :visible="true"
          width="100%"
          height="100%"
          @close="workspace.clear()"
        />
      </div>
    </div>

    <!-- Welcome Screen (Project Selection) -->
    <div v-else-if="!selectedProject" class="h-full flex flex-col items-center justify-center px-8 text-center overflow-y-auto">
      <h2 class="text-3xl font-semibold text-white mb-10 tracking-tight max-w-3xl">
        Pick a folder to be the predominant knowledge base for your chat
      </h2>

      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mt-4 max-w-6xl w-full">
        <!-- Existing project cards -->
        <button
          v-for="project in assignedProjects"
          :key="project.id"
          @click="selectProject(project)"
          :class="[
            'group relative p-6 rounded-2xl transition-all duration-300 ease-out card-tile border-2',
            selectedProjectId === project.id 
              ? 'border-purple-500/80 tile-active' 
              : 'border-purple-500/40 tile-idle'
          ]"
        >
          <div class="text-center space-y-2">
            <div :class="[
              'w-16 h-16 mx-auto rounded-2xl flex items-center justify-center transition-all duration-300 text-white',
              selectedProjectId === project.id ? 'bg-gradient-to-br from-purple-500 to-purple-700 shadow-lg' : 'bg-gradient-to-br from-purple-400 to-purple-600 group-hover:shadow-lg'
            ]">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p class="font-semibold text-white text-lg">{{ project.id }}</p>
            <p class="text-sm text-white/70">{{ project.name }}</p>
          </div>
        </button>

        <!-- User-added folder cards -->
        <div
          v-for="project in savedFolders"
          :key="project.id"
          :class="[
            'group relative rounded-2xl transition-all duration-300 ease-out card-tile border-2',
            selectedProjectId === project.id 
              ? 'border-purple-500/80 tile-active' 
              : 'border-purple-500/40 tile-idle'
          ]"
        >
          <button
            @click="selectProject(project)"
            class="w-full p-6 text-center"
          >
            <div class="space-y-2">
              <div :class="[
                'w-16 h-16 mx-auto rounded-2xl flex items-center justify-center transition-all duration-300 text-white',
                selectedProjectId === project.id ? 'bg-gradient-to-br from-purple-500 to-purple-700 shadow-lg' : 'bg-gradient-to-br from-purple-400 to-purple-600 group-hover:shadow-lg'
              ]">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <p class="font-semibold text-white text-lg">{{ project.id }}</p>
              <p class="text-sm text-white/70 truncate max-w-[150px] mx-auto" :title="project.localPath">{{ project.name }}</p>
            </div>
          </button>
          <button
            @click.stop="removeFolder(project.id)"
            class="absolute top-2 right-2 w-6 h-6 rounded-full bg-red-500/20 hover:bg-red-500/40 text-red-400 flex items-center justify-center opacity-0 group-hover:opacity-100 transition z-10"
            title="Remove folder"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Add Folder Button -->
        <button
          @click="showFolderBrowser = true"
          class="group relative p-6 rounded-2xl transition-all duration-300 ease-out card-tile border-2 border-dashed border-white/20 hover:border-purple-500/50 hover:bg-white/5"
        >
          <div class="text-center space-y-2">
            <div class="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center transition-all duration-300 text-white bg-gradient-to-br from-purple-400/20 to-purple-600/20 group-hover:from-purple-400/40 group-hover:to-purple-600/40">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <p class="font-semibold text-white text-lg">Add Folder</p>
            <p class="text-sm text-white/70">Browse and select</p>
          </div>
        </button>
      </div>
    </div>

    <!-- Project Overview (for assigned projects without localPath) -->
    <div v-else-if="selectedProject && !selectedProject.localPath && !selectedTask" class="h-full px-8 py-8 space-y-6 overflow-y-auto">
      <div class="flex flex-col gap-2">
        <button 
          @click="clearSelection"
          class="inline-flex items-center gap-2 text-white/60 hover:text-white transition text-sm self-start"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Projects
        </button>
        <div class="inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white px-4 py-2 rounded-lg shadow-lg">
          <span class="text-xs uppercase tracking-wide">Tasks / Work / {{ selectedProject.id }}</span>
        </div>
        <h1 class="text-3xl font-semibold text-white">Project Overview</h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Completed Tasks -->
        <div class="card-pane p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-white">Completed</h2>
            <span class="text-sm text-white/60">{{ completedTasks.length }} tasks</span>
          </div>
          <ul class="space-y-2">
            <li v-for="task in completedTasks" :key="task.id" class="flex items-center gap-2 text-white/85">
              <span class="text-purple-300">✓</span>
              <span>{{ task.name }}</span>
            </li>
          </ul>
          <div class="h-32 bg-[#0c0c0c] rounded-xl flex items-end justify-around p-3 border border-white/5">
            <div class="bg-purple-400 w-10 rounded-t" style="height: 40%"></div>
            <div class="bg-purple-500 w-10 rounded-t" style="height: 60%"></div>
            <div class="bg-purple-600 w-10 rounded-t" style="height: 80%"></div>
            <div class="bg-purple-700 w-10 rounded-t" style="height: 100%"></div>
          </div>
        </div>

        <!-- To-Do Tasks -->
        <div class="card-pane p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-white">To-Do</h2>
            <span class="text-sm text-white/60">{{ todoTasks.length }} tasks</span>
          </div>
          <ul class="space-y-2">
            <li
              v-for="task in todoTasks"
              :key="task.id"
              @click="selectTask(task)"
              :class="[
                'cursor-pointer px-3 py-2 rounded-lg transition border border-transparent',
                task.id === selectedTaskId ? 'bg-purple-700/40 border-purple-500/40 text-white' : 'bg-white/5 text-white/80 hover:bg-white/8 hover:border-white/10'
              ]"
            >
              {{ task.name }}
            </li>
          </ul>
          <div class="h-32 flex items-center justify-center">
            <div class="w-28 h-28 rounded-full bg-gradient-to-br from-purple-500 via-purple-600 to-purple-800 shadow-lg"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Detail View - Workspace Area -->
    <div v-else-if="selectedTask" class="h-full flex flex-col px-8 py-8 space-y-6 overflow-y-auto">
      <div class="flex-shrink-0 space-y-3">
        <div class="inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white px-4 py-2 rounded-lg shadow-lg">
          <span class="text-xs uppercase tracking-wide">Tasks / Work / {{ selectedProject?.id }} / {{ selectedTask.name }}</span>
        </div>
        <h1 class="text-3xl font-semibold text-white tracking-tight">{{ selectedTask.name }}</h1>
      </div>

      <!-- Workspace Content Area - Shows PDF, Draft, Model, or Empty State -->
      <div class="flex-1 min-h-0 card-pane overflow-hidden">
        <!-- PDF Viewer -->
        <PDFViewer
          v-if="workspaceState.mode === 'pdf'"
          :pdf-url="workspaceState.pdfUrl"
          :file-url="workspaceState.pdfUrl"
          :file-name="workspaceState.pdfFileName"
          @close="workspace.clear()"
        />

        <!-- Draft Editor -->
        <DraftEditor
          v-else-if="workspaceState.mode === 'draft'"
          :title="workspaceState.draftTitle"
          :initial-content="workspaceState.draftContent"
          :loading="draftLoading"
          :loading-message="draftLoadingMessage"
          @update:content="workspace.updateDraftContent"
          @export-word="handleExportToWord"
          @close="workspace.clear()"
        />

        <!-- Model Viewer -->
        <SpeckleViewer
          v-else-if="workspaceState.mode === 'model'"
          :model-url="workspaceState.modelUrl || selectedTask.modelUrl"
          :model-name="workspaceState.modelName || selectedProject?.name || selectedTask?.name || 'Model'"
          :visible="true"
          width="100%"
          height="100%"
          @close="workspace.clear()"
        />

        <!-- Empty State / Task Details -->
        <div v-else class="h-full bg-[#0f0f0f] rounded-2xl p-8 flex flex-col gap-6">
          <p class="text-white/80 text-lg font-semibold">
            Let's get started—use the chat to tell Sid what you need.
          </p>

          <!-- Task Details -->
          <div class="space-y-6">
            <div v-if="selectedTask.goal" class="bg-purple-900/30 border border-purple-500/40 rounded-lg p-4">
              <h3 class="font-semibold text-white mb-2">Goal</h3>
              <p class="text-white/80">{{ selectedTask.goal }}</p>
            </div>

            <div v-if="selectedTask.features" class="bg-white/5 rounded-lg p-5 border border-white/10">
              <h3 class="font-semibold text-white mb-3 text-lg">Features</h3>
              <ul class="space-y-2">
                <li v-for="(value, key) in selectedTask.features" :key="key" class="flex justify-between items-center py-2 border-b border-white/10 last:border-b-0 text-white/80">
                  <span class="font-medium text-white">{{ key }}:</span>
                  <span>{{ value || '(blank)' }}</span>
                </li>
              </ul>
            </div>

            <!-- Quick Actions -->
            <div class="p-5 bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg shadow-lg flex items-center justify-between">
              <div>
                <h4 class="font-semibold text-white mb-1 text-lg">Quick Actions</h4>
                <p class="text-white/80 text-sm">Jump straight into the model or keep drafting.</p>
              </div>
              <div class="flex gap-3">
                <button
                  v-if="selectedTask.modelUrl"
                  @click="workspace.openModel(selectedTask.modelUrl, selectedProject?.name)"
                  class="px-4 py-2 bg-white/15 hover:bg-white/25 text-white rounded-lg font-semibold transition-all duration-200 border border-white/20 flex items-center gap-2"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Show 3D Model
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Folder Browser Modal -->
    <FolderBrowserModal
      v-if="showFolderBrowser"
      @close="showFolderBrowser = false"
      @select="handleFolderSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SpeckleViewer from '~/components/SpeckleViewer.vue'
import PDFViewer from '~/components/PDFViewer.vue'
import DraftEditor from '~/components/DraftEditor.vue'
import FolderBrowserModal from '~/components/FolderBrowserModal.vue'
import ProjectWorkspaceView from '~/components/ProjectWorkspaceView.vue'
import { useWorkspace } from '~/composables/useWorkspace'

const workspace = useWorkspace()
const workspaceState = computed(() => workspace.state.value)
const draftLoading = ref(false)
const draftLoadingMessage = ref('')
const showFolderBrowser = ref(false)

interface Project {
  id: string
  name: string
  localPath?: string
  type?: 'assigned' | 'folder'
}

interface Task {
  id: string
  name: string
  goal?: string
  features?: Record<string, string>
  modelUrl?: string
}

const selectedProjectId = ref<string | null>(null)
const selectedProject = ref<Project | null>(null)
const selectedTaskId = ref<string | null>(null)
const selectedTask = ref<Task | null>(null)

// Saved folders from localStorage
const savedFolders = ref<Project[]>([])
const STORAGE_KEY_FOLDERS = 'work-folders-v1'

function loadSavedFolders() {
  if (typeof window === 'undefined') return
  try {
    const stored = localStorage.getItem(STORAGE_KEY_FOLDERS)
    if (stored) {
      savedFolders.value = JSON.parse(stored)
    }
  } catch (error) {
    console.error('Error loading saved folders:', error)
  }
}

function saveFolders() {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY_FOLDERS, JSON.stringify(savedFolders.value))
  } catch (error) {
    console.error('Error saving folders:', error)
  }
}

function addFolder(project: Project) {
  // Check if folder already exists
  if (savedFolders.value.some(p => p.localPath === project.localPath)) {
    console.log('Folder already exists:', project.localPath)
    return
  }
  savedFolders.value.push(project)
  saveFolders()
}

function removeFolder(projectId: string) {
  savedFolders.value = savedFolders.value.filter(p => p.id !== projectId)
  saveFolders()
  if (selectedProjectId.value === projectId) {
    clearSelection()
  }
}

function handleFolderSelected(path: string, name: string) {
  const project: Project = {
    id: name,
    name: name,
    localPath: path,
    type: 'folder'
  }
  addFolder(project)
  showFolderBrowser.value = false
}

function clearSelection() {
  selectedProject.value = null
  selectedProjectId.value = null
  selectedTask.value = null
  selectedTaskId.value = null
}

function handleExportToWord(content: string) {
  console.log('Export to Word requested:', content)
}

// Assigned projects (empty by default, can be populated from API)
const assignedProjects: Project[] = []

const completedTasks: Task[] = [
  { id: 'task1', name: 'Preliminary Layout' },
  { id: 'task2', name: 'Beam Sizing' }
]

const todoTasks: Task[] = [
  { id: 'task3', name: 'Finish Foundation Design' },
  { id: 'task4', name: 'Retaining Wall Design' },
  { id: 'task5', name: 'Model Truss Framing'},
  { id: 'task6', name: 'QA/QC' }
]

const emit = defineEmits<{
  'update-breadcrumb': [breadcrumb: string]
}>()

function selectProject(project: Project) {
  selectedProject.value = project
  selectedProjectId.value = project.id
  selectedTask.value = null
  selectedTaskId.value = null
  emit('update-breadcrumb', `Tasks/Work/${project.id}`)
}

function selectTask(task: Task) {
  selectedTask.value = task
  selectedTaskId.value = task.id
  if (selectedProject.value) {
    emit('update-breadcrumb', `Tasks/Work/${selectedProject.value.id}/${task.name}`)
  }
}

onMounted(() => {
  loadSavedFolders()
})
</script>

<style scoped>
.work-view {
  background: #0f0f0f;
  color: #fff;
}

.card-pane {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.card-tile {
  background: #111;
  box-shadow: 0 14px 50px rgba(0, 0, 0, 0.45);
}

.tile-active {
  border-color: rgba(124, 58, 237, 0.8);
  box-shadow: 0 18px 60px rgba(124, 58, 237, 0.35);
}

.tile-idle:hover {
  border-color: rgba(255, 255, 255, 0.16);
  transform: translateY(-2px);
}

.work-view :deep([class*="text-gray-900"]),
.work-view :deep([class*="text-gray-800"]),
.work-view :deep([class*="text-gray-700"]) {
  color: #fff !important;
}

.work-view :deep([class*="text-gray-600"]) {
  color: rgba(255, 255, 255, 0.85) !important;
}

.work-view :deep([class*="text-gray-500"]),
.work-view :deep([class*="text-gray-400"]),
.work-view :deep([class*="text-gray-300"]) {
  color: rgba(255, 255, 255, 0.65) !important;
}

.work-view :deep([class*="bg-white"]),
.work-view :deep([class*="bg-gray-1"]),
.work-view :deep([class*="bg-gray-2"]),
.work-view :deep([class*="bg-gray-3"]) {
  background-color: #131313 !important;
  color: #fff;
}

.work-view :deep([class*="bg-gray-5"]) {
  background-color: #0f0f0f !important;
}

.work-view :deep([class*="border-gray-"]) {
  border-color: rgba(255, 255, 255, 0.14) !important;
}

.work-view :deep(.shadow-xl),
.work-view :deep(.shadow-lg),
.work-view :deep(.shadow-2xl) {
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.45) !important;
}
</style>
