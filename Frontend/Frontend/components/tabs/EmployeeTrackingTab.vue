<template>
  <div class="h-full w-full flex flex-col bg-foundation overflow-hidden">
    <!-- Header -->
    <div class="border-b border-foundation-line bg-foundation-2 p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-2xl font-bold">Employee Productivity Dashboard</h2>
          <p class="text-sm text-foreground-muted mt-1">
            Time tracking overview for all team members
          </p>
        </div>
        <TimeScaleToggle v-model="timeScale" />
      </div>

      <!-- Search -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search employees by name or role..."
          class="w-full max-w-md pl-10 pr-4 py-2 rounded-lg border border-foundation-line bg-foundation text-foreground placeholder-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </div>

    <!-- Employee Cards Grid + Detail Panel -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <EmployeeCard
          v-for="employee in displayEmployees"
          :key="employee.id"
          :employee="employee"
          :time-scale="timeScale"
          @click="handleEmployeeClick(employee)"
        />
      </div>

      <div
        v-if="displayEmployees.length === 0"
        class="text-center py-12"
      >
        <p class="text-foreground-muted">No employees found matching your search.</p>
      </div>

      <!-- Timesheet Log / Project Metrics detail, inspired by v0 drill-down pages -->
      <div
        v-if="selectedEmployee"
        class="mt-4 grid grid-cols-1 xl:grid-cols-3 gap-6"
      >
        <!-- Summary + project metrics -->
        <div class="xl:col-span-1 space-y-4">
          <div class="bg-foundation-2 border border-foundation-line rounded-lg p-5">
            <div class="flex items-center justify-between mb-2">
              <div>
                <h3 class="text-lg font-semibold text-foreground">
                  {{ selectedEmployee.name }}
                </h3>
                <p class="text-xs text-foreground-muted mt-1">
                  {{ selectedEmployee.role }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-xs text-foreground-muted">
                  Weekly Hours
                </p>
                <p class="text-2xl font-bold text-foreground">
                  {{ selectedEmployee.weeklyHours }}h
                </p>
              </div>
            </div>
            <p class="text-xs text-foreground-muted mt-3">
              This detail view is powered by the same sample timesheet data as the original v0 demo,
              showing how automatic logs can roll up into project metrics.
            </p>
          </div>

          <div class="bg-foundation-2 border border-foundation-line rounded-lg p-5">
            <h4 class="text-sm font-semibold text-foreground mb-3">
              Key Projects (sample)
            </h4>
            <div
              v-if="relatedProjects.length === 0"
              class="text-xs text-foreground-muted"
            >
              No related projects found in the sample data.
            </div>
            <div
              v-else
              class="space-y-3"
            >
              <div
                v-for="project in relatedProjects"
                :key="project.id"
                class="flex items-start justify-between text-xs"
              >
                <div>
                  <p class="font-medium text-foreground">
                    {{ project.id }} · {{ project.name }}
                  </p>
                  <p class="text-foreground-muted">
                    {{ project.totalHours }}h total ·
                    <span v-if="project.status">
                      {{ project.status }}
                    </span>
                    <span v-else>
                      Sample project
                    </span>
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-foreground-muted">
                    {{ project.employees.find(e => e.id === selectedEmployee.id)?.hours ?? '—' }}h
                  </p>
                  <p class="text-foreground-muted">
                    by {{ selectedEmployee.name.split(' ')[0] }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Timesheet log -->
        <div class="xl:col-span-2 bg-foundation-2 border border-foundation-line rounded-lg p-5">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h4 class="text-sm font-semibold text-foreground">
                Timesheet Log (sample week)
              </h4>
              <p class="text-xs text-foreground-muted">
                Auto-captured events grouped by project, task, and app.
              </p>
            </div>
          </div>

          <div class="overflow-x-auto -mx-3 sm:mx-0">
            <table class="min-w-full text-xs">
              <thead>
                <tr class="text-left text-foreground-muted border-b border-foundation-line">
                  <th class="py-2 pr-4 font-medium">
                    Date / Time
                  </th>
                  <th class="py-2 pr-4 font-medium">
                    Project
                  </th>
                  <th class="py-2 pr-4 font-medium">
                    Task / Subtask
                  </th>
                  <th class="py-2 pr-4 font-medium">
                    App
                  </th>
                  <th class="py-2 pr-4 font-medium text-right">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="event in selectedEmployeeEvents"
                  :key="`${event.employeeId}-${event.startTime}-${event.task}-${event.subtask}`"
                  class="border-b border-foundation-line/60 last:border-b-0"
                >
                  <td class="py-2 pr-4 whitespace-nowrap">
                    <div class="text-foreground">
                      {{ new Date(event.timestamp).toLocaleDateString() }}
                    </div>
                    <div class="text-foreground-muted">
                      {{ new Date(event.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                      –
                      {{ new Date(event.endTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                    </div>
                  </td>
                  <td class="py-2 pr-4">
                    <div class="text-foreground">
                      {{ event.project }}
                    </div>
                  </td>
                  <td class="py-2 pr-4">
                    <div class="text-foreground">
                      {{ event.task }}
                    </div>
                    <div class="text-foreground-muted">
                      {{ event.subtask }}
                    </div>
                  </td>
                  <td class="py-2 pr-4">
                    <span class="text-foreground-muted">
                      {{ event.app }}
                    </span>
                  </td>
                  <td class="py-2 pr-0 text-right">
                    <span class="font-medium text-foreground">
                      {{ Math.round(event.duration / 60 * 10) / 10 }}h
                    </span>
                  </td>
                </tr>

                <tr v-if="selectedEmployeeEvents.length === 0">
                  <td
                    colspan="5"
                    class="py-6 text-center text-foreground-muted"
                  >
                    No sample timesheet events are available yet for this employee.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { employees, type Employee } from '~/data/employees'
import { timeEvents, timeProjects, type TimeEvent, type TimeProject } from '~/data/timeTracking'
import EmployeeCard from '~/components/EmployeeCard.vue'
import TimeScaleToggle from '~/components/TimeScaleToggle.vue'

type TimeScale = 'weekly' | 'monthly' | 'yearly'

const searchQuery = ref('')
const timeScale = ref<TimeScale>('weekly')

// Selected employee for drill-down log view
const selectedEmployeeId = ref<string | null>(null)

const filteredEmployees = computed(() => {
  const query = searchQuery.value.toLowerCase()
  return employees.filter(
    (emp) =>
      emp.name.toLowerCase().includes(query) ||
      emp.role.toLowerCase().includes(query)
  )
})

const displayEmployees = computed(() => {
  return filteredEmployees.value.map((emp) => {
    let hours = emp.weeklyHours
    let breakdown = emp.weeklyBreakdown

    if (timeScale.value === 'monthly') {
      if (emp.monthlyBreakdown) {
        breakdown = emp.monthlyBreakdown
        hours = emp.monthlyHours || breakdown.reduce((sum, item) => sum + item.value, 0)
      } else {
        hours = Math.round(emp.weeklyHours * 4.33)
        breakdown = emp.weeklyBreakdown.map((item) => ({
          ...item,
          value: Math.round(item.value * 4.33),
        }))
      }
    } else if (timeScale.value === 'yearly') {
      if (emp.yearlyBreakdown) {
        breakdown = emp.yearlyBreakdown
        hours = emp.yearlyHours || breakdown.reduce((sum, item) => sum + item.value, 0)
      } else {
        hours = Math.round(emp.weeklyHours * 52)
        breakdown = emp.weeklyBreakdown.map((item) => ({
          ...item,
          value: Math.round(item.value * 52),
        }))
      }
    }

    return {
      ...emp,
      weeklyHours: hours,
      weeklyBreakdown: breakdown,
    }
  })
})

const selectedEmployee = computed<Employee | null>(() => {
  if (!selectedEmployeeId.value) return null
  return employees.find((e) => e.id === selectedEmployeeId.value) || null
})

// Events for the selected employee (simple weekly log for now)
const selectedEmployeeEvents = computed<TimeEvent[]>(() => {
  if (!selectedEmployeeId.value) return []
  return timeEvents
    .filter((e) => e.employeeId === selectedEmployeeId.value)
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
})

const relatedProjects = computed<TimeProject[]>(() => {
  if (!selectedEmployeeId.value) return []
  const employeeProjects = new Set(
    timeEvents
      .filter((e) => e.employeeId === selectedEmployeeId.value && e.project && e.project !== 'Admin' && e.project !== 'Unknown')
      .map((e) => e.project),
  )
  return timeProjects.filter((p) => employeeProjects.has(p.id))
})

function handleEmployeeClick(emp: Employee) {
  selectedEmployeeId.value = emp.id === selectedEmployeeId.value ? null : emp.id
}
</script>

