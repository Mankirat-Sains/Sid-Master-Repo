<template>
  <div class="h-full">
    <!-- Welcome Screen (Project Selection) - Modern Apple-like Design -->
    <div v-if="!selectedProject" class="h-full flex flex-col items-center justify-center px-8">
      <h2 class="text-4xl font-light text-gray-900 mb-16 tracking-tight" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">
        Select one of the projects you have been assigned and get to work
      </h2>
      
      <div class="grid grid-cols-4 gap-8 mt-8 max-w-6xl">
        <button
          v-for="project in assignedProjects"
          :key="project.id"
          @click="selectProject(project)"
          :class="[
            'group relative p-8 rounded-3xl transition-all duration-300 ease-out backdrop-blur-sm',
            selectedProjectId === project.id
              ? 'bg-white/80 shadow-2xl scale-105 border border-gray-200/50'
              : 'bg-white/40 hover:bg-white/60 hover:scale-105 hover:shadow-xl border border-transparent hover:border-gray-200/50'
          ]"
        >
          <div class="text-center">
            <div :class="[
              'w-20 h-20 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-all duration-300',
              selectedProjectId === project.id
                ? 'bg-gradient-to-br from-purple-500 to-purple-700 shadow-lg'
                : 'bg-gradient-to-br from-purple-400 to-purple-600 group-hover:shadow-lg'
            ]">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p class="font-medium text-gray-900 text-lg mb-1" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ project.id }}</p>
            <p class="text-sm text-gray-600 font-light" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ project.name }}</p>
          </div>
        </button>
      </div>
    </div>

    <!-- Workspace Content (shown when workspace has content, even without selected task) -->
    <div v-else-if="workspaceState.mode !== 'empty'" class="h-full flex flex-col">
      <div class="flex-1 min-h-0 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl overflow-hidden border border-gray-200/50">
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

    <!-- Project Overview -->
    <div v-else-if="selectedProject && !selectedTask" class="h-full px-8 py-8">
      <div class="mb-8">
        <div class="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-5 py-2.5 rounded-xl inline-block mb-5 shadow-lg">
          <span class="font-medium text-sm tracking-wide">Tasks/Work/{{ selectedProject.id }}</span>
        </div>
        <h1 class="text-4xl font-light text-gray-900 tracking-tight" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">Project Overview</h1>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <!-- Completed Tasks -->
        <div class="bg-white/60 backdrop-blur-xl rounded-2xl p-8 shadow-lg border border-gray-200/50">
          <h2 class="text-2xl font-light text-gray-900 mb-6 tracking-tight" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">Completed</h2>
          <ul class="space-y-2 mb-6">
            <li v-for="task in completedTasks" :key="task.id" class="text-gray-700">
              ✓ {{ task.name }}
            </li>
          </ul>
          <!-- Bar Chart Placeholder -->
          <div class="h-48 bg-gray-100 rounded flex items-end justify-around p-4">
            <div class="bg-purple-400 w-12 rounded-t" style="height: 40%"></div>
            <div class="bg-purple-500 w-12 rounded-t" style="height: 60%"></div>
            <div class="bg-purple-600 w-12 rounded-t" style="height: 80%"></div>
            <div class="bg-purple-700 w-12 rounded-t" style="height: 100%"></div>
          </div>
        </div>

        <!-- To-Do Tasks -->
        <div class="bg-white/60 backdrop-blur-xl rounded-2xl p-8 shadow-lg border border-gray-200/50">
          <h2 class="text-2xl font-light text-gray-900 mb-6 tracking-tight" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">To-Do</h2>
          <ul class="space-y-2 mb-6">
            <li
              v-for="task in todoTasks"
              :key="task.id"
              @click="selectTask(task)"
              :class="[
                'text-gray-700 cursor-pointer hover:text-purple-600 transition-colors',
                task.id === selectedTaskId ? 'text-purple-600 font-semibold' : ''
              ]"
            >
              {{ task.name }}
            </li>
          </ul>
          <!-- Pie Chart Placeholder -->
          <div class="h-48 flex items-center justify-center">
            <div class="w-32 h-32 rounded-full bg-gradient-to-br from-purple-400 via-purple-600 to-purple-800"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Detail View - Workspace Area -->
    <div v-else-if="selectedTask" class="h-full flex flex-col px-8 py-8">
      <div class="mb-8 flex-shrink-0">
        <div class="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-5 py-2.5 rounded-xl inline-block mb-5 shadow-lg">
          <span class="font-medium text-sm tracking-wide">Tasks/Work/{{ selectedProject.id }}/{{ selectedTask.name }}</span>
        </div>
        <h1 class="text-4xl font-light text-gray-900 tracking-tight" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ selectedTask.name }}</h1>
      </div>

      <!-- Workspace Content Area - Shows PDF, Draft, Model, or Empty State -->
      <div class="flex-1 min-h-0 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl overflow-hidden border border-gray-200/50">
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
        <div v-else class="h-full bg-white/60 backdrop-blur-xl rounded-2xl p-8 shadow-lg border border-gray-200/50 flex items-center justify-center">
          <p class="text-gray-700 text-xl font-light tracking-wide" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">
            Let's Get Started...Type in the Chat What you Want to Do
          </p>
          
          <!-- Task Details -->
          <div class="space-y-6">
            <div v-if="selectedTask.goal" class="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
              <h3 class="font-bold text-gray-800 mb-2">Goal: {{ selectedTask.goal }}</h3>
            </div>
            
            <div v-if="selectedTask.features" class="bg-gray-50 rounded-lg p-6">
              <h3 class="font-bold text-gray-800 mb-4 text-lg">Features:</h3>
              <ul class="space-y-2">
                <li v-for="(value, key) in selectedTask.features" :key="key" class="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                  <span class="font-medium text-gray-700">{{ key }}:</span>
                  <span class="text-gray-600">{{ value || '(blank)' }}</span>
                </li>
              </ul>
            </div>

            <!-- Quick Actions -->
            <div class="p-6 bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg shadow-lg">
              <h4 class="font-semibold text-white mb-4 text-lg">Quick Actions</h4>
              <div class="flex gap-3">
                <button
                  v-if="selectedTask.modelUrl"
                  @click="workspace.openModel(selectedTask.modelUrl, selectedProject?.name)"
                  class="px-6 py-3 bg-white hover:bg-gray-100 text-purple-700 rounded-lg font-semibold transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105 flex items-center gap-2"
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

