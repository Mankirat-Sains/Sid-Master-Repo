<template>
  <div 
    class="h-screen w-screen flex flex-col bg-gradient-to-br from-[#050507] via-[#0b0f1a] to-[#0f0a1b] overflow-hidden relative text-white"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseUp"
  >
    <!-- Ambient glows -->
    <div class="pointer-events-none absolute inset-0">
      <div class="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-purple-700/25 blur-3xl"></div>
      <div class="absolute right-[-14rem] top-10 h-[30rem] w-[30rem] rounded-full bg-purple-400/18 blur-[180px]"></div>
      <div class="absolute left-1/3 bottom-0 h-72 w-72 rounded-full bg-indigo-400/12 blur-[140px]"></div>
      <div class="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-black/40"></div>
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.04),transparent_35%),radial-gradient(circle_at_80%_10%,rgba(255,255,255,0.04),transparent_32%)]"></div>
    </div>
    <!-- Tasks Panel (Top Slider) - Only covers left panel, not chat -->
    <div
      v-if="tasksPanelOpen"
      class="absolute top-0 left-0 border-b border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.55)] z-30 transition-all backdrop-blur-xl bg-[#0f1224]/90"
      :style="{ 
        height: `${tasksPanelHeight}px`, 
        maxHeight: '60vh', 
        minHeight: '120px',
        width: `calc(100% - ${chatPanelWidth}px)`,
        right: 'auto',
        backgroundColor: 'rgba(15, 18, 36, 0.92)',
        backdropFilter: 'blur(20px)'
      }"
    >
      <!-- Navigation: WORK, TIMESHEET, TO-DO LIST, DISCUSSION, SETTINGS -->
      <div class="bg-white/5 backdrop-blur-sm border-b border-white/10 px-8 py-5 flex items-center justify-center gap-6 relative">
        <button
          v-for="navItem in navItems"
          :key="navItem.id"
          @click="activeNav = navItem.id; tasksPanelOpen = false"
          :class="[
            'flex flex-col items-center gap-2 px-5 py-3 rounded-xl transition-all duration-200 border',
            activeNav === navItem.id
              ? 'bg-gradient-to-r from-purple-500 to-purple-400 text-black shadow-lg shadow-purple-900/50 scale-105 border-purple-200/60'
              : 'text-gray-200 hover:text-white hover:bg-white/10 hover:border-white/10 border-transparent'
          ]"
          style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
        >
          <component :is="navItem.icon" :class-name="activeNav === navItem.id ? 'w-6 h-6' : 'w-5 h-5'" />
          <span class="text-xs font-semibold tracking-wide">{{ navItem.label }}</span>
        </button>
        
        <button
          @click="tasksPanelOpen = false"
          class="absolute right-6 p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-300 hover:text-white"
          title="Close Tasks"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Resize Handle (bottom edge) -->
      <div
        class="absolute bottom-0 left-0 right-0 h-1 bg-white/10 cursor-ns-resize hover:bg-purple-400 transition-colors"
        @mousedown="(e) => handleTasksResizeStart(e, tasksPanelHeight)"
      ></div>
    </div>

    <!-- Main Content Area -->
    <div 
      class="flex-1 flex overflow-hidden relative z-10"
    >
      <!-- Document List Panel (Left Side, Resizable) -->
      <DocumentListPanel
        v-if="documentsListOpen"
        :is-open="documentsListOpen"
        :title="documentsListTitle"
        :subtitle="documentsListSubtitle"
        :documents="similarDocuments"
        :width="documentsListWidth"
        @close="documentsListOpen = false"
        @select-document="handleDocumentSelect"
        @resize="documentsListWidth = $event"
      />

      <!-- Left Main Panel - With Tasks and Logs panels -->
      <div 
        class="flex-1 flex flex-col bg-transparent overflow-hidden relative"
        :style="{ 
          marginTop: tasksPanelOpen ? `${tasksPanelHeight}px` : '0',
          marginLeft: documentsListOpen ? `${documentsListWidth}px` : '0'
        }"
      >
        <!-- Tasks Toggle Button (when closed) - Positioned over left panel only -->
        <button
          v-if="!tasksPanelOpen"
          @click="tasksPanelOpen = true"
          class="absolute top-2 left-1/2 transform -translate-x-1/2 bg-[#121527]/90 backdrop-blur-lg hover:bg-[#171b31] text-gray-100 hover:text-white px-6 py-2.5 rounded-b-xl shadow-lg shadow-purple-900/40 transition-all z-40 flex items-center gap-2 border-b-2 border-purple-500/60 border border-white/10"
          title="Show Tasks"
          style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span class="font-semibold text-sm">Tasks</span>
        </button>

        <!-- Breadcrumb Bar -->
        <div v-if="breadcrumb" class="bg-white/5 backdrop-blur-sm border-b border-white/10 px-8 py-3 flex items-center gap-3 text-sm text-gray-200">
          <svg class="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span class="font-medium" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">{{ breadcrumb }}</span>
        </div>

        <!-- Content based on active nav -->
        <div class="flex-1 overflow-auto bg-gradient-to-br from-[#0c0f1c] via-[#0c0f20] to-[#120c24] p-8 text-gray-100">
          <!-- Welcome Screen (shown when no active nav) -->
          <WelcomeScreen v-if="!activeNav" />
          
          <!-- WORK View (shows projects only when work is active) -->
          <WorkView v-else-if="activeNav === 'work'" @update-breadcrumb="breadcrumb = $event" />
          
          <!-- TIMESHEET View -->
          <TimesheetView v-else-if="activeNav === 'timesheet'" />
          
          <!-- TO-DO LIST View -->
          <TodoListView v-else-if="activeNav === 'todo'" />
          
          <!-- DISCUSSION View -->
          <DiscussionView v-else-if="activeNav === 'discussion'" />
          
          <!-- SETTINGS View -->
          <SettingsView v-else-if="activeNav === 'settings'" />
        </div>


        <!-- Logs Toggle Button (when closed) - Positioned over left panel only -->
        <button
          v-if="!logsPanelOpen"
          @click="logsPanelOpen = true"
          class="absolute bottom-2 left-1/2 transform -translate-x-1/2 bg-[#121527]/90 backdrop-blur-lg hover:bg-[#171b31] text-gray-100 hover:text-white px-6 py-2.5 rounded-t-xl shadow-lg shadow-purple-900/40 transition-all z-40 flex items-center gap-2 border-t-2 border-purple-500/60 border border-white/10"
          title="Show Agent Logs"
          style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="font-semibold text-sm">Logs</span>
          <span v-if="agentLogs.length > 0" class="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs font-semibold border border-purple-200">
            {{ agentLogs.length }}
          </span>
        </button>
      </div>

      <!-- Right Chat Panel (Resizable) - Always visible, never covered -->
      <div 
        class="bg-[#0e1023]/90 backdrop-blur-xl border-l border-white/10 relative flex-shrink-0 shadow-[0_10px_60px_rgba(0,0,0,0.6)]"
        :style="{ width: `${chatPanelWidth}px`, minWidth: '320px', maxWidth: '50%' }"
      >
        <SmartChatPanel @agent-log="handleAgentLog" @first-message-sent="handleFirstMessage" />
        
        <!-- Resize Handle (left edge) -->
        <div
          class="absolute left-0 top-0 bottom-0 w-1 bg-white/10 cursor-ew-resize hover:bg-purple-500 transition-colors"
          @mousedown="(e) => handleChatResizeStart(e, chatPanelWidth)"
        ></div>
      </div>
    </div>

    <!-- Agent Logs Panel (Bottom Slider, Draggable & Resizable) - Spans across bottom, aligned with chat panel -->
    <AgentLogsPanel
      v-if="logsPanelOpen"
      :is-open="logsPanelOpen"
      :logs="agentLogs"
      :panel-height="logsPanelHeight"
      :panel-bottom="logsPanelBottom"
      :chat-panel-width="chatPanelWidth"
      @close="logsPanelOpen = false"
      @resize-start="handleLogsResizeStart"
      @drag-start="handleLogsDragStart"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, provide } from 'vue'
import SmartChatPanel from '~/components/SmartChatPanel.vue'
import AgentLogsPanel, { type AgentLog } from '~/components/AgentLogsPanel.vue'
import DocumentListPanel from '~/components/DocumentListPanel.vue'
import FolderIcon from '~/components/icons/FolderIcon.vue'
import ClockIcon from '~/components/icons/ClockIcon.vue'
import ClipboardIcon from '~/components/icons/ClipboardIcon.vue'
import ChatIcon from '~/components/icons/ChatIcon.vue'
import GearIcon from '~/components/icons/GearIcon.vue'
import { useWorkspace } from '~/composables/useWorkspace'
import { useRuntimeConfig } from '#app'

const activeNav = ref<'work' | 'timesheet' | 'todo' | 'discussion' | 'settings' | null>(null)
const tasksPanelOpen = ref(false)
const logsPanelOpen = ref(false) // Hidden by default
const breadcrumb = ref<string | null>(null)
const agentLogs = ref<AgentLog[]>([])

// Document list panel
const documentsListOpen = ref(false)
const documentsListTitle = ref('Similar Projects')
const documentsListSubtitle = ref('')
const similarDocuments = ref<any[]>([])
const documentsListWidth = ref(400)

// Panel sizes
const tasksPanelHeight = ref(180)
const chatPanelWidth = ref(420)
const logsPanelHeight = ref(320)
const logsPanelBottom = ref(0) // Position from bottom (0 = at bottom)

// Workspace management
const workspace = useWorkspace()
const config = useRuntimeConfig()

// Resizing state
const resizingPanel = ref<'tasks' | 'chat' | 'logs' | null>(null)
const draggingPanel = ref<'logs' | null>(null)
const resizeStartPos = ref(0)
const resizeStartSize = ref(0)
const dragStartPos = ref(0)
const dragStartBottom = ref(0)

// Navigation items with icons
const navItems = [
  {
    id: 'work',
    label: 'WORK',
    icon: FolderIcon
  },
  {
    id: 'timesheet',
    label: 'TIMESHEET',
    icon: ClockIcon
  },
  {
    id: 'todo',
    label: 'TO-DO LIST',
    icon: ClipboardIcon
  },
  {
    id: 'discussion',
    label: 'DISCUSSION',
    icon: ChatIcon
  },
  {
    id: 'settings',
    label: 'SETTINGS',
    icon: GearIcon
  }
]

function handleTasksResizeStart(e: MouseEvent, currentHeight: number) {
  resizingPanel.value = 'tasks'
  resizeStartPos.value = e.clientY
  resizeStartSize.value = currentHeight
  e.preventDefault()
  e.stopPropagation()
}

function handleChatResizeStart(e: MouseEvent, currentWidth: number) {
  resizingPanel.value = 'chat'
  resizeStartPos.value = e.clientX
  resizeStartSize.value = currentWidth
  e.preventDefault()
  e.stopPropagation()
}

function handleLogsResizeStart(e: MouseEvent, currentHeight: number) {
  resizingPanel.value = 'logs'
  resizeStartPos.value = e.clientY
  resizeStartSize.value = currentHeight
  e.preventDefault()
  e.stopPropagation()
}

function handleLogsDragStart(e: MouseEvent, currentBottom: number) {
  draggingPanel.value = 'logs'
  dragStartPos.value = e.clientY
  dragStartBottom.value = currentBottom
  e.preventDefault()
  e.stopPropagation()
}

function handleMouseMove(e: MouseEvent) {
  if (draggingPanel.value === 'logs') {
    // Dragging: move panel up/down
    const delta = dragStartPos.value - e.clientY // Inverted: moving mouse up increases bottom offset
    const maxBottom = window.innerHeight - logsPanelHeight.value - 50 // Max position (leave some space at top)
    const newBottom = Math.max(0, Math.min(maxBottom, dragStartBottom.value + delta))
    logsPanelBottom.value = newBottom
  } else if (resizingPanel.value === 'tasks') {
    const delta = e.clientY - resizeStartPos.value
    const newHeight = Math.max(120, Math.min(window.innerHeight * 0.6, resizeStartSize.value + delta))
    tasksPanelHeight.value = newHeight
  } else if (resizingPanel.value === 'chat') {
    const delta = resizeStartPos.value - e.clientX
    const newWidth = Math.max(320, Math.min(window.innerWidth * 0.5, resizeStartSize.value + delta))
    chatPanelWidth.value = newWidth
  } else if (resizingPanel.value === 'logs') {
    // Resizing: adjust panel height
    const delta = resizeStartPos.value - e.clientY // Inverted: moving mouse up increases height
    const maxHeight = window.innerHeight - logsPanelBottom.value - 20 // Leave some margin
    const newHeight = Math.max(200, Math.min(maxHeight, resizeStartSize.value + delta))
    logsPanelHeight.value = newHeight
  }
}

function handleMouseUp() {
  resizingPanel.value = null
  draggingPanel.value = null
}

function handleAgentLog(log: AgentLog) {
  agentLogs.value.unshift(log)
  if (agentLogs.value.length > 50) {
    agentLogs.value = agentLogs.value.slice(0, 50)
  }
  if (!logsPanelOpen.value) {
    logsPanelOpen.value = true
  }
}

function handleFirstMessage() {
  // Hide welcome screen by setting activeNav to 'work'
  if (!activeNav.value) {
    activeNav.value = 'work'
  }
}

function handleDocumentSelect(document: any) {
  // Ensure work view is active to show the viewer
  if (!activeNav.value || activeNav.value !== 'work') {
    activeNav.value = 'work'
  }
  
  // Check if this is a Speckle model (has projectId and modelId in metadata)
  if (document.metadata?.projectId && document.metadata?.modelId) {
    // Open Speckle model in workspace
    // Use document.url if available (already constructed with correct server URL)
    // Otherwise construct URL using configured Speckle server
    const modelUrl = document.url || `${config.public.speckleUrl}/projects/${document.metadata.projectId}/models/${document.metadata.modelId}`
    console.log('Opening Speckle model:', { 
      modelUrl, 
      document,
      speckleUrl: config.public.speckleUrl,
      projectId: document.metadata.projectId,
      modelId: document.metadata.modelId
    })
    workspace.openModel(modelUrl, document.title || document.name)
  } else if (document.url || document.filePath) {
    // Open PDF in workspace
    workspace.openPDF(document.url || document.filePath, document.title || document.name)
  }
}

// Expose workspace methods for chat to use
provide('workspace', workspace)
provide('emitAgentLog', handleAgentLog)
provide('openDocumentsList', (documents: any[], title?: string, subtitle?: string) => {
  similarDocuments.value = documents
  documentsListTitle.value = title || 'Documents'
  documentsListSubtitle.value = subtitle || ''
  documentsListOpen.value = true
})
provide('openPDF', (url: string, fileName?: string) => {
  workspace.openPDF(url, fileName)
})
provide('openDraft', (title: string, content?: string) => {
  workspace.openDraft(title, content)
})
provide('openModel', (url: string, name?: string) => {
  workspace.openModel(url, name)
})
provide('similarDocuments', similarDocuments)

// Lazy load view components
const WelcomeScreen = defineAsyncComponent(() => import('~/components/WelcomeScreen.vue'))
const WorkView = defineAsyncComponent(() => import('~/components/views/WorkView.vue'))
const TimesheetView = defineAsyncComponent(() => import('~/components/views/TimesheetView.vue'))
const TodoListView = defineAsyncComponent(() => import('~/components/views/TodoListView.vue'))
const DiscussionView = defineAsyncComponent(() => import('~/components/views/DiscussionView.vue'))
const SettingsView = defineAsyncComponent(() => import('~/components/views/SettingsView.vue'))
</script>
