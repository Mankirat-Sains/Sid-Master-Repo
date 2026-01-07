<template>
  <div class="h-full work-view bg-[#0f0f0f] text-white overflow-y-auto">
    <!-- Workspace Content (shown when workspace has content - takes priority) -->
    <div v-if="workspaceState.mode !== 'empty'" class="h-full flex flex-col">
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
    <div v-else-if="!selectedProject" class="h-full flex flex-col items-center justify-center px-8 text-center">
      <h2 class="text-3xl font-semibold text-white mb-10 tracking-tight max-w-3xl">
        Select one of the projects you have been assigned and get to work
      </h2>

      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mt-4 max-w-6xl w-full">
        <button
          v-for="project in assignedProjects"
          :key="project.id"
          @click="selectProject(project)"
          :class="[
            'group relative p-6 rounded-2xl transition-all duration-300 ease-out card-tile',
            selectedProjectId === project.id ? 'tile-active' : 'tile-idle'
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
      </div>
    </div>

    <!-- Project Overview -->
    <div v-else-if="selectedProject && !selectedTask" class="h-full px-8 py-8 space-y-6">
      <div class="flex flex-col gap-2">
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
    <div v-else-if="selectedTask" class="h-full flex flex-col px-8 py-8 space-y-6">
      <div class="flex-shrink-0 space-y-3">
        <div class="inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white px-4 py-2 rounded-lg shadow-lg">
          <span class="text-xs uppercase tracking-wide">Tasks / Work / {{ selectedProject.id }} / {{ selectedTask.name }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SpeckleViewer from '~/components/SpeckleViewer.vue'
import PDFViewer from '~/components/PDFViewer.vue'
import DraftEditor from '~/components/DraftEditor.vue'
import { useWorkspace } from '~/composables/useWorkspace'

const workspace = useWorkspace()
const workspaceState = computed(() => workspace.state.value)
const draftLoading = ref(false)
const draftLoadingMessage = ref('')

interface Project {
  id: string
  name: string
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

function handleExportToWord(content: string) {
  // This will be handled by the chat/local agent integration
  console.log('Export to Word requested:', content)
  // TODO: Emit event to parent or call local agent API
}

async function handleAIAddSection(prompt: string, currentContent: string) {
  console.log('AI Add Section requested:', prompt)
  
  draftLoading.value = true
  draftLoadingMessage.value = 'Generating new section with AI...'
  
  try {
    // Construct the message for the AI to generate a new section
    const message = `${prompt}

Current proposal content:
${currentContent.substring(0, 2000)}...

Please generate the new section in HTML format with proper formatting:
- Use <h2> for section headings
- Use <p> for paragraphs
- Use <ul> and <li> for bullet lists
- Use <strong> for bold text
- Ensure the HTML is valid and well-formatted

Return only the HTML content for the new section, without any additional explanation.`
    
    const response = await sendChatMessage(message, 'draft-ai-edit')
    
    // Extract HTML from response - try to find HTML content
    let htmlContent = response.reply
    
    // If response is wrapped in markdown code blocks, extract HTML
    const codeBlockMatch = htmlContent.match(/```(?:html)?\s*([\s\S]*?)\s*```/)
    if (codeBlockMatch) {
      htmlContent = codeBlockMatch[1]
    }
    
    // Ensure it's valid HTML - if it starts with a tag, use as-is
    if (!htmlContent.trim().startsWith('<')) {
      // Wrap in paragraph if it's plain text
      htmlContent = `<p>${htmlContent}</p>`
    }
    
    // Insert the content into the draft editor
    if (draftEditorRef.value && typeof draftEditorRef.value.insertContentAtCursor === 'function') {
      draftEditorRef.value.insertContentAtCursor(htmlContent)
    } else {
      // Fallback: append to current content
      const updatedContent = currentContent + '\n\n' + htmlContent
      workspace.updateDraftContent(updatedContent)
    }
  } catch (error) {
    console.error('AI add section error:', error)
    alert('Error generating section. Please try again.')
  } finally {
    draftLoading.value = false
    draftLoadingMessage.value = ''
  }
}

// Mock assigned projects
const assignedProjects: Project[] = [
  { id: '2025-01-004', name: 'Downtown Office Tower' },
  { id: '2025-03-006', name: 'Industrial Warehouse' },
  { id: '2025-07-006', name: 'School Addition' },
  { id: '2025-09-006', name: 'Retail Complex' }
]

const completedTasks: Task[] = [
  { id: 'task1', name: 'Preliminary Layout' },
  { id: 'task2', name: 'Beam Sizing' }
]

const todoTasks: Task[] = [
  { id: 'task3', name: 'Finish Foundation Design' },
  { id: 'task4', name: 'Retaining Wall Design' },
  { 
    id: 'task5', 
    name: 'Model Truss Framing',
    goal: 'Find past similar projects',
    modelUrl: 'https://app.speckle.systems/projects/bde23c9150/models/fc47277266',
    features: {
      'Span': '10m',
      'Loading': 'OBC',
      'Location': 'Trout Lake',
      'Width': '',
      'Bridge type': ''
    }
  },
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
  border: 1px solid rgba(255, 255, 255, 0.08);
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
