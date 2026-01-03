<template>
  <div class="h-full w-full flex flex-col bg-foundation overflow-hidden">
    <!-- Header -->
    <div class="border-b border-foundation-line bg-foundation-2 p-6">
      <div>
        <h2 class="text-2xl font-bold">Command Center</h2>
        <p class="text-sm text-foreground-muted mt-1">
          Unified overview of BIM queries, document analysis, and team productivity
        </p>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="flex-1 overflow-y-auto p-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- Recent Activity -->
        <div class="lg:col-span-2 bg-foundation-2 border border-foundation-line rounded-lg p-6">
          <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
          <div class="space-y-4">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="flex items-start gap-4 p-4 bg-foundation rounded-lg"
            >
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center"
                :class="activity.type === 'bim' ? 'bg-purple-500/20 text-purple-400' : activity.type === 'document' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'"
              >
                <span class="text-xl">{{ activity.icon }}</span>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-foreground">{{ activity.title }}</p>
                <p class="text-xs text-foreground-muted mt-1">{{ activity.description }}</p>
                <p class="text-xs text-foreground-muted mt-2">{{ formatTime(activity.timestamp) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="space-y-6">
          <!-- BIM Queries -->
          <div class="bg-foundation-2 border border-foundation-line rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">BIM Queries</h3>
            <div class="space-y-3">
              <div>
                <p class="text-3xl font-bold text-foreground">{{ stats.bimQueries }}</p>
                <p class="text-sm text-foreground-muted">Today</p>
              </div>
              <div class="pt-3 border-t border-foundation-line">
                <p class="text-xl font-semibold text-foreground">{{ stats.bimQueriesWeek }}</p>
                <p class="text-sm text-foreground-muted">This Week</p>
              </div>
            </div>
          </div>

          <!-- Document Analysis -->
          <div class="bg-foundation-2 border border-foundation-line rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Document Analysis</h3>
            <div class="space-y-3">
              <div>
                <p class="text-3xl font-bold text-foreground">{{ stats.documentQueries }}</p>
                <p class="text-sm text-foreground-muted">Today</p>
              </div>
              <div class="pt-3 border-t border-foundation-line">
                <p class="text-xl font-semibold text-foreground">{{ stats.documentQueriesWeek }}</p>
                <p class="text-sm text-foreground-muted">This Week</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Team Productivity Summary -->
      <div class="bg-foundation-2 border border-foundation-line rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4">Team Productivity Summary</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p class="text-sm text-foreground-muted mb-2">Total Team Hours (This Week)</p>
            <p class="text-2xl font-bold text-foreground">{{ teamStats.totalHours }}h</p>
          </div>
          <div>
            <p class="text-sm text-foreground-muted mb-2">Active Projects</p>
            <p class="text-2xl font-bold text-foreground">{{ teamStats.activeProjects }}</p>
          </div>
          <div>
            <p class="text-sm text-foreground-muted mb-2">Team Members</p>
            <p class="text-2xl font-bold text-foreground">{{ teamStats.teamMembers }}</p>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-6 bg-foundation-2 border border-foundation-line rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            @click="$emit('navigate', 'bim')"
            class="p-4 bg-primary/10 hover:bg-primary/20 border border-primary/30 rounded-lg transition-colors text-left"
          >
            <p class="font-medium text-foreground">View BIM Models</p>
            <p class="text-sm text-foreground-muted mt-1">Query and explore 3D models</p>
          </button>
          <button
            @click="$emit('navigate', 'documents')"
            class="p-4 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 rounded-lg transition-colors text-left"
          >
            <p class="font-medium text-foreground">Query Documents</p>
            <p class="text-sm text-foreground-muted mt-1">Ask questions about PDFs and drawings</p>
          </button>
          <button
            @click="$emit('navigate', 'employees')"
            class="p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg transition-colors text-left"
          >
            <p class="font-medium text-foreground">View Team Dashboard</p>
            <p class="text-sm text-foreground-muted mt-1">Track employee productivity</p>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { employees } from '~/data/employees'

defineEmits<{
  navigate: [tab: string]
}>()

interface Activity {
  id: string
  type: 'bim' | 'document' | 'employee'
  title: string
  description: string
  timestamp: Date
  icon: string
}

const recentActivities = ref<Activity[]>([
  {
    id: '1',
    type: 'bim',
    title: 'BIM Model Query',
    description: 'Asked about structural elements in Project 25-08-127',
    timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
    icon: '🏗️',
  },
  {
    id: '2',
    type: 'document',
    title: 'Document Analysis',
    description: 'Queried technical drawing for foundation specifications',
    timestamp: new Date(Date.now() - 1000 * 60 * 45), // 45 minutes ago
    icon: '📄',
  },
  {
    id: '3',
    type: 'employee',
    title: 'Team Update',
    description: 'Employee productivity tracked - 42 hours this week',
    timestamp: new Date(Date.now() - 1000 * 60 * 120), // 2 hours ago
    icon: '👥',
  },
])

const stats = ref({
  bimQueries: 12,
  bimQueriesWeek: 47,
  documentQueries: 8,
  documentQueriesWeek: 32,
})

const teamStats = ref({
  totalHours: employees.reduce((sum, emp) => sum + emp.weeklyHours, 0),
  activeProjects: 7,
  teamMembers: employees.length,
})

function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffMins < 60) {
    return `${diffMins} minutes ago`
  } else if (diffHours < 24) {
    return `${diffHours} hours ago`
  } else {
    return date.toLocaleDateString()
  }
}
</script>

