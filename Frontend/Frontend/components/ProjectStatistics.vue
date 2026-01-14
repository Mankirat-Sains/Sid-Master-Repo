<template>
  <div class="h-full flex flex-col bg-[#0a0a0a] text-white overflow-hidden">
    <!-- Header -->
    <div class="flex-shrink-0 px-6 py-4 border-b border-white/10 bg-[#111]">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-white">Project Statistics</h2>
          <p class="text-xs text-white/50 mt-1">{{ stats.projectName }}</p>
        </div>
        <button
          @click="$emit('close')"
          class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition flex items-center justify-center"
          title="Close statistics"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scroll">
      <!-- Overview Cards -->
      <div class="grid grid-cols-2 gap-4">
        <div class="stat-card">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white/60 text-sm">Total Files</span>
            <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <p class="text-3xl font-bold text-white">{{ stats.totalFiles }}</p>
          <p class="text-xs text-white/40 mt-1">{{ stats.totalFolders }} folders • {{ formatSize(stats.totalSize) }}</p>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white/60 text-sm">Total Hours</span>
            <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-3xl font-bold text-white">{{ stats.totalHours.toFixed(1) }}</p>
          <p class="text-xs text-white/40 mt-1">{{ stats.hoursThisWeek.toFixed(1) }}h this week</p>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white/60 text-sm">Completion</span>
            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-3xl font-bold text-white">{{ stats.completionPercentage }}%</p>
          <p class="text-xs mt-1" :class="getStatusTextClass(stats.projectStatus)">
            {{ formatStatus(stats.projectStatus) }}
          </p>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white/60 text-sm">Tasks</span>
            <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p class="text-3xl font-bold text-white">{{ stats.completedTasks }}/{{ stats.tasks.length }}</p>
          <p class="text-xs text-white/40 mt-1">{{ stats.inProgressTasks }} in progress</p>
        </div>
      </div>

      <!-- Progress Chart -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
          Project Progress & Projections
        </h3>
        <div class="h-48 relative">
          <svg class="w-full h-full" viewBox="0 0 600 180">
            <!-- Grid lines -->
            <line v-for="i in 5" :key="`grid-${i}`" :x1="60" :y1="i * 36" :x2="580" :y2="i * 36" stroke="rgba(255,255,255,0.05)" stroke-width="1" />
            
            <!-- Y-axis labels -->
            <text v-for="(val, i) in [100, 75, 50, 25, 0]" :key="`y-${i}`" :x="50" :y="i * 36 + 5" fill="rgba(255,255,255,0.4)" font-size="10" text-anchor="end">
              {{ val }}%
            </text>
            
            <!-- X-axis labels -->
            <text v-for="(week, i) in stats.weeklyProgress" :key="`x-${i}`" :x="60 + i * (520 / (stats.weeklyProgress.length - 1))" y="170" fill="rgba(255,255,255,0.4)" font-size="10" text-anchor="middle">
              Week {{ week.week }}
            </text>
            
            <!-- Planned line (dashed) -->
            <polyline
              :points="getLinePoints(stats.weeklyProgress.map(w => w.plannedCompletion))"
              fill="none"
              stroke="rgba(147, 51, 234, 0.5)"
              stroke-width="2"
              stroke-dasharray="4,4"
            />
            
            <!-- Actual line (solid) -->
            <polyline
              :points="getLinePoints(stats.weeklyProgress.map(w => w.actualCompletion))"
              fill="none"
              stroke="#a855f7"
              stroke-width="3"
            />
            
            <!-- Projected line (dotted) -->
            <polyline
              :points="getLinePoints(stats.weeklyProgress.map(w => w.projectedCompletion))"
              fill="none"
              stroke="#22c55e"
              stroke-width="2"
              stroke-dasharray="2,2"
            />
            
            <!-- Data points on actual line -->
            <circle
              v-for="(week, i) in stats.weeklyProgress"
              :key="`point-${i}`"
              :cx="60 + i * (520 / (stats.weeklyProgress.length - 1))"
              :cy="160 - (week.actualCompletion / 100) * 140"
              r="4"
              fill="#a855f7"
            />
          </svg>
        </div>
        <div class="flex items-center gap-6 mt-4 text-xs">
          <div class="flex items-center gap-2">
            <div class="w-6 h-0.5 bg-purple-400/50" style="border-top: 2px dashed rgba(147, 51, 234, 0.5);"></div>
            <span class="text-white/60">Planned</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-6 h-1 bg-purple-500 rounded-full"></div>
            <span class="text-white/60">Actual</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-6 h-0.5 bg-green-500" style="border-top: 2px dotted #22c55e;"></div>
            <span class="text-white/60">Projected</span>
          </div>
        </div>
      </div>

      <!-- File Types Distribution -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          File Distribution
        </h3>
        <div class="space-y-3">
          <div v-for="fileType in stats.fileTypes" :key="fileType.type" class="flex items-center gap-3">
            <div class="w-20 text-xs text-white/60 font-mono">{{ fileType.type }}</div>
            <div class="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden relative">
              <div
                class="h-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
                :style="{ width: `${(fileType.count / stats.totalFiles) * 100}%` }"
              ></div>
              <div class="absolute inset-0 flex items-center justify-between px-3">
                <span class="text-xs text-white font-semibold">{{ fileType.count }} files</span>
                <span class="text-xs text-white/60">{{ formatSize(fileType.totalSize) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Time Tracking by User -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          Time by Team Member
        </h3>
        <div class="space-y-3">
          <div v-for="(user, i) in stats.timeByUser" :key="i" class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
              {{ getUserInitials(user.user) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm text-white font-medium">{{ user.user }}</span>
                <span class="text-sm text-white/60">{{ user.hours.toFixed(1) }}h</span>
              </div>
              <div class="h-2 bg-white/5 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
                  :style="{ width: `${(user.hours / stats.totalHours) * 100}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tasks List -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          Tasks & Priorities
        </h3>
        <div class="space-y-2">
          <div
            v-for="task in sortedTasks"
            :key="task.id"
            :class="[
              'p-3 rounded-lg border transition cursor-pointer hover:bg-white/5',
              task.status === 'completed' ? 'bg-white/[0.02] border-white/5 opacity-60' : 'bg-white/5 border-white/10'
            ]"
          >
            <div class="flex items-start gap-3">
              <input
                type="checkbox"
                :checked="task.status === 'completed'"
                class="mt-0.5 w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500 focus:ring-offset-0 cursor-pointer"
                @change="toggleTask(task.id)"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h4 :class="['text-sm font-medium', task.status === 'completed' ? 'text-white/50 line-through' : 'text-white']">
                    {{ task.title }}
                  </h4>
                  <span
                    :class="[
                      'px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0',
                      getPriorityClass(task.priority)
                    ]"
                  >
                    {{ task.priority }}
                  </span>
                </div>
                <p class="text-xs text-white/50 mb-2">{{ task.description }}</p>
                <div class="flex items-center gap-4 text-xs text-white/40">
                  <span class="flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {{ task.estimatedHours }}h
                  </span>
                  <span class="flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(task.dueDate) }}
                  </span>
                  <span v-if="task.assignee" class="flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {{ task.assignee }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Modifications -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Recent Modifications
          <span class="ml-auto text-xs text-white/40">{{ stats.modificationsThisWeek }} this week</span>
        </h3>
        <div class="space-y-3">
          <div v-for="mod in stats.recentModifications.slice(0, 6)" :key="mod.id" class="flex gap-3 p-3 bg-white/5 rounded-lg border border-white/10">
            <div :class="[
              'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
              mod.action === 'created' ? 'bg-green-500/20 text-green-400' : 
              mod.action === 'modified' ? 'bg-blue-500/20 text-blue-400' : 
              'bg-red-500/20 text-red-400'
            ]">
              <svg v-if="mod.action === 'created'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              <svg v-else-if="mod.action === 'modified'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-white truncate">{{ mod.fileName }}</span>
                <span class="text-xs text-white/40 flex-shrink-0 ml-2">{{ formatTimestamp(mod.timestamp) }}</span>
              </div>
              <p class="text-xs text-white/60 mb-1">{{ mod.summary }}</p>
              <div class="flex items-center gap-2 text-xs text-white/40">
                <span>{{ mod.user }}</span>
                <span>•</span>
                <span>{{ mod.filesAffected }} file{{ mod.filesAffected > 1 ? 's' : '' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Project Projection -->
      <div class="stat-card">
        <h3 class="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          Project Forecast
        </h3>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
            <div>
              <p class="text-xs text-white/60 mb-1">Projected Completion Date</p>
              <p class="text-lg font-semibold text-white">{{ formatDate(stats.projectedCompletionDate) }}</p>
            </div>
            <div :class="['px-3 py-1 rounded-full text-xs font-semibold', getStatusBadgeClass(stats.projectStatus)]">
              {{ formatStatus(stats.projectStatus) }}
            </div>
          </div>
          
          <div class="grid grid-cols-3 gap-3">
            <div class="p-3 bg-white/5 rounded-lg border border-white/10 text-center">
              <p class="text-2xl font-bold text-green-400">{{ stats.completedTasks }}</p>
              <p class="text-xs text-white/60 mt-1">Completed</p>
            </div>
            <div class="p-3 bg-white/5 rounded-lg border border-white/10 text-center">
              <p class="text-2xl font-bold text-yellow-400">{{ stats.inProgressTasks }}</p>
              <p class="text-xs text-white/60 mt-1">In Progress</p>
            </div>
            <div class="p-3 bg-white/5 rounded-lg border border-white/10 text-center">
              <p class="text-2xl font-bold text-blue-400">{{ stats.notStartedTasks }}</p>
              <p class="text-xs text-white/60 mt-1">Not Started</p>
            </div>
          </div>

          <div class="p-4 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-lg border border-purple-500/30">
            <p class="text-sm text-white/90 leading-relaxed">
              <strong>Analysis:</strong> Based on current velocity, the project is on track to complete by {{ formatDate(stats.projectedCompletionDate) }}. 
              {{ getRiskAnalysis() }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FolderStatistics, TaskItem } from '~/data/folderStatistics'
import { sampleFolderStatistics } from '~/data/folderStatistics'

defineProps<{
  projectId: string
  rootPath: string
}>()

defineEmits<{
  close: []
}>()

// In production, this would be fetched from an API based on projectId and rootPath
const stats = ref<FolderStatistics>(sampleFolderStatistics)

const sortedTasks = computed(() => {
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  return [...stats.value.tasks].sort((a, b) => {
    // Completed tasks go to bottom
    if (a.status === 'completed' && b.status !== 'completed') return 1
    if (a.status !== 'completed' && b.status === 'completed') return -1
    // Then sort by priority
    return priorityOrder[a.priority] - priorityOrder[b.priority]
  })
})

function getLinePoints(values: number[]): string {
  return values
    .map((val, i) => {
      const x = 60 + i * (520 / (values.length - 1))
      const y = 160 - (val / 100) * 140
      return `${x},${y}`
    })
    .join(' ')
}

function formatSize(mb: number): string {
  if (mb >= 1000) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb.toFixed(1)} MB`
}

function formatStatus(status: string): string {
  const map: Record<string, string> = {
    'on-track': 'On Track',
    'at-risk': 'At Risk',
    'behind': 'Behind',
    'ahead': 'Ahead of Schedule'
  }
  return map[status] || status
}

function getStatusTextClass(status: string): string {
  const map: Record<string, string> = {
    'on-track': 'text-blue-400',
    'at-risk': 'text-yellow-400',
    'behind': 'text-red-400',
    'ahead': 'text-green-400'
  }
  return map[status] || 'text-white/60'
}

function getStatusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    'on-track': 'bg-blue-500/20 text-blue-400',
    'at-risk': 'bg-yellow-500/20 text-yellow-400',
    'behind': 'bg-red-500/20 text-red-400',
    'ahead': 'bg-green-500/20 text-green-400'
  }
  return map[status] || 'bg-white/10 text-white/60'
}

function getPriorityClass(priority: TaskItem['priority']): string {
  const map: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400',
    high: 'bg-orange-500/20 text-orange-400',
    medium: 'bg-yellow-500/20 text-yellow-400',
    low: 'bg-green-500/20 text-green-400'
  }
  return map[priority] || 'bg-white/10 text-white/60'
}

function getUserInitials(name: string): string {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function toggleTask(taskId: string) {
  const task = stats.value.tasks.find(t => t.id === taskId)
  if (task) {
    task.status = task.status === 'completed' ? 'in-progress' : 'completed'
    // Update counters
    stats.value.completedTasks = stats.value.tasks.filter(t => t.status === 'completed').length
    stats.value.inProgressTasks = stats.value.tasks.filter(t => t.status === 'in-progress').length
    stats.value.notStartedTasks = stats.value.tasks.filter(t => t.status === 'not-started').length
  }
}

function getRiskAnalysis(): string {
  const { projectStatus, completionPercentage, inProgressTasks } = stats.value
  
  if (projectStatus === 'ahead') {
    return 'Excellent progress! Continue current pace to finish early.'
  }
  if (projectStatus === 'on-track') {
    return `With ${completionPercentage}% complete, maintain current velocity to meet deadline.`
  }
  if (projectStatus === 'at-risk') {
    return `${inProgressTasks} tasks in progress. Consider allocating additional resources to critical path items.`
  }
  return 'Project is behind schedule. Immediate attention needed on high-priority tasks.'
}
</script>

<style scoped>
.stat-card {
  @apply bg-[#111] border border-white/10 rounded-xl p-5 shadow-lg;
}

.custom-scroll::-webkit-scrollbar {
  width: 8px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
