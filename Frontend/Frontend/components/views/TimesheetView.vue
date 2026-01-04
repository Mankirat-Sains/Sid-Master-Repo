<template>
  <div class="h-full w-full flex bg-gradient-to-br from-slate-50 to-white overflow-hidden">
    <!-- Left sidebar nav (mirrors v0: Employees, Projects, Insights, etc.) -->
    <aside class="w-56 border-r border-gray-200 bg-white/80 backdrop-blur-xl flex flex-col">
      <div class="px-4 py-4 border-b border-gray-200">
        <p class="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
          IanAnalytics (IA)
        </p>
        <p class="text-sm text-gray-700">
          Engineering Tracking System
        </p>
      </div>
      <nav class="flex-1 py-4 space-y-1 text-sm">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          class="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-left transition-colors"
          :class="activeSection === item.id ? 'bg-purple-100 text-purple-700 font-medium' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
          @click="handleNavClick(item.id)"
        >
          <span class="inline-block w-5 text-center">
            {{ item.icon }}
          </span>
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </aside>

    <!-- Right content area -->
    <div class="flex-1 flex flex-col bg-gradient-to-br from-slate-50 to-white overflow-hidden">
      <!-- Header + search -->
      <header class="border-b border-gray-200 bg-white/80 backdrop-blur-xl p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-3xl font-bold text-gray-900">{{ headerTitle }}</h2>
            <p class="text-sm text-gray-500 mt-1">
              {{ headerSubtitle }}
            </p>
          </div>
          <TimeScaleToggle v-model="timeScale" />
        </div>

        <!-- Search (employees section only) -->
        <div
          v-if="activeSection === 'employees'"
          class="relative"
        >
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search employees by name or role..."
            class="w-full max-w-md pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 backdrop-blur-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
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
      </header>

      <!-- Main content: either dashboard list or drill-down detail, similar to v0 routing -->
      <main class="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-br from-slate-50/50 to-white/50">
        <!-- Employees dashboard (v0 /app/page) -->
        <section
          v-if="activeSection === 'employees' && !selectedEmployee"
          class="space-y-6"
        >
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
            <p class="text-gray-500">No employees found matching your search.</p>
          </div>
        </section>

        <!-- Employee detail view (v0 /employees/[id]) -->
        <section
          v-else-if="activeSection === 'employees' && selectedEmployee"
          class="space-y-4"
        >
          <button
            type="button"
            class="text-xs text-gray-500 hover:text-gray-900 underline transition-colors"
            @click="selectedEmployeeId = null"
          >
            ← Back to all employees
          </button>

          <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <!-- Left column: summary + project metrics -->
            <div class="xl:col-span-1 space-y-4">
              <div class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
                <div class="flex items-center justify-between mb-2">
                  <div>
                    <h3 class="text-lg font-semibold text-gray-900">
                      {{ selectedEmployee.name }}
                    </h3>
                    <p class="text-xs text-gray-500 mt-1">
                      {{ selectedEmployee.role }}
                    </p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">
                      Weekly Hours
                    </p>
                    <p class="text-2xl font-bold text-gray-900">
                      {{ selectedEmployee.weeklyHours }}h
                    </p>
                  </div>
                </div>
                <p class="text-xs text-gray-500 mt-3">
                  Detail view driven by the same sample project and timesheet data as the original v0 demo.
                </p>
              </div>

              <div class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
                <h4 class="text-sm font-semibold text-gray-900 mb-3">
                  Key Projects
                </h4>
                <div
                  v-if="relatedProjects.length === 0"
                  class="text-xs text-gray-500"
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
                      <p class="font-medium text-gray-900">
                        {{ project.id }} · {{ project.name }}
                      </p>
                      <p class="text-gray-500">
                        {{ project.totalHours }}h total
                        <span v-if="project.status">
                          · {{ project.status }}
                        </span>
                      </p>
                    </div>
                    <div class="text-right">
                      <p class="text-gray-500">
                        {{
                          project.employees.find((e) => e.id === selectedEmployee.id)?.hours ??
                          '—'
                        }}h
                      </p>
                      <p class="text-gray-500">
                        by {{ selectedEmployee.name.split(' ')[0] }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right column: detailed timesheet log -->
            <div class="xl:col-span-2 bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <h4 class="text-sm font-semibold text-gray-900">
                    Timesheet Log (sample week)
                  </h4>
                  <p class="text-xs text-gray-500">
                    Auto-captured events grouped by project, task, and app – copied from the v0 demo
                    dataset.
                  </p>
                </div>
              </div>

              <div class="overflow-x-auto -mx-3 sm:mx-0">
                <table class="min-w-full text-xs">
                  <thead>
                    <tr class="text-left text-gray-500 border-b border-gray-200">
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
                      class="border-b border-gray-200/60 last:border-b-0 hover:bg-gray-50/50 transition-colors"
                    >
                      <td class="py-2 pr-4 whitespace-nowrap">
                        <div class="text-gray-900">
                          {{ new Date(event.timestamp).toLocaleDateString() }}
                        </div>
                        <div class="text-gray-500">
                          {{
                            new Date(event.startTime).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          }}
                          –
                          {{
                            new Date(event.endTime).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          }}
                        </div>
                      </td>
                      <td class="py-2 pr-4">
                        <div class="text-gray-900">
                          {{ event.project }}
                        </div>
                      </td>
                      <td class="py-2 pr-4">
                        <div class="text-gray-900">
                          {{ event.task }}
                        </div>
                        <div class="text-gray-500">
                          {{ event.subtask }}
                        </div>
                      </td>
                      <td class="py-2 pr-4">
                        <span class="text-gray-500">
                          {{ event.app }}
                        </span>
                      </td>
                      <td class="py-2 pr-0 text-right">
                        <span class="font-medium text-gray-900">
                          {{ Math.round((event.duration / 60) * 10) / 10 }}h
                        </span>
                      </td>
                    </tr>

                    <tr v-if="selectedEmployeeEvents.length === 0">
                      <td
                        colspan="5"
                        class="py-6 text-center text-gray-500"
                      >
                        No sample timesheet events are available yet for this employee.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <!-- Projects overview (v0 /projects) -->
        <section
          v-else-if="activeSection === 'projects'"
          class="space-y-6"
        >
          <div
            v-for="project in timeProjects"
            :key="project.id"
            class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 grid grid-cols-1 md:grid-cols-2 gap-6 shadow-xl"
          >
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs border border-gray-300 bg-gray-100 text-gray-700">
                  {{ project.id }}
                </span>
                <span class="text-xs text-gray-500">
                  {{ project.totalHours }}h total
                </span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ project.name }}
              </h3>
              <div class="mt-4">
                <p class="text-xs font-semibold text-gray-500 mb-2">
                  Team Members
                </p>
                <div class="space-y-2">
                  <div
                    v-for="member in project.employees"
                    :key="member.id"
                    class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50/80 backdrop-blur-sm border border-gray-200"
                  >
                    <span class="text-sm text-gray-900">
                      {{ member.name }}
                    </span>
                    <span class="text-sm font-medium text-gray-900">
                      {{ member.hours }}h
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Simple task distribution bars -->
            <div class="space-y-3">
              <p class="text-sm font-semibold text-gray-900 mb-1">
                Task Distribution
              </p>
              <div class="space-y-2">
                <div
                  v-for="task in project.tasks"
                  :key="task.name"
                  class="space-y-1"
                >
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-500 truncate">
                      {{ task.name }}
                    </span>
                    <span class="text-gray-900">
                      {{ task.value }}h
                    </span>
                  </div>
                  <div class="h-2 rounded-full bg-gray-200 overflow-hidden">
                    <div
                      class="h-full rounded-full bg-gradient-to-r from-purple-500 to-purple-600"
                      :style="{ width: `${(task.value / project.totalHours) * 100}%` }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Project insights table (v0 /insights) -->
        <section
          v-else-if="activeSection === 'projectInsights'"
          class="space-y-4"
        >
          <div class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">
              Project Performance Table
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full text-xs">
                <thead>
                  <tr class="text-left text-gray-500 border-b border-gray-200">
                    <th class="py-2 pr-4 font-medium">Project ID</th>
                    <th class="py-2 pr-4 font-medium">Project Name</th>
                    <th class="py-2 pr-4 font-medium">Planned Hours</th>
                    <th class="py-2 pr-4 font-medium">Actual Hours</th>
                    <th class="py-2 pr-4 font-medium">% Complete</th>
                    <th class="py-2 pr-4 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="proj in projectInsights"
                    :key="proj.id"
                    class="border-b border-gray-200/60 last:border-b-0 hover:bg-gray-50/50 transition-colors"
                  >
                    <td class="py-2 pr-4">
                      <span class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[11px] border border-gray-300 bg-gray-100 text-gray-700">
                        {{ proj.id }}
                      </span>
                    </td>
                    <td class="py-2 pr-4 text-gray-900">
                      {{ proj.name }}
                    </td>
                    <td class="py-2 pr-4 text-gray-900">
                      {{ proj.plannedHours }}h
                    </td>
                    <td class="py-2 pr-4 text-gray-900">
                      {{ proj.actualHours }}h
                    </td>
                    <td class="py-2 pr-4 text-gray-900">
                      {{ proj.percentComplete }}%
                    </td>
                    <td class="py-2 pr-4 text-right">
                      <span
                        class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[11px] font-medium"
                        :class="statusClass(proj.status)"
                      >
                        {{ proj.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- Simple Employee Insights section (billable vs non-billable with bar graph-style rows) -->
        <section
          v-else-if="activeSection === 'employeeInsights'"
          class="space-y-4"
        >
          <div class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">
              Billable vs Non-billable Hours by Employee
            </h3>
            <p class="text-xs text-gray-500 mb-4">
              Approximate mix of billable vs non-billable time for each engineer. This mirrors the
              skills/insights view from the v0 system in a compact format.
            </p>
            <div class="space-y-3">
              <div
                v-for="emp in employees"
                :key="emp.id"
                class="space-y-1"
              >
                <div class="flex items-center justify-between text-xs">
                  <span class="text-gray-900">{{ emp.name }}</span>
                  <span class="text-gray-500">
                    {{ emp.yearlyHours || emp.weeklyHours * 52 }}h / year
                  </span>
                </div>

                <div class="h-3 w-full rounded-full bg-gray-200 overflow-hidden flex">
                  <div
                    class="h-full bg-emerald-500"
                    :style="{ width: `${billableRatio(emp) * 100}%` }"
                  />
                  <div
                    class="h-full bg-amber-500"
                    :style="{ width: `${(1 - billableRatio(emp)) * 100}%` }"
                  />
                </div>

                <div class="flex items-center justify-between text-[11px] text-gray-500">
                  <span>
                    Billable:
                    <strong>{{ Math.round(billableHours(emp)) }}h</strong>
                  </span>
                  <span>
                    Non-billable:
                    <strong>{{ Math.round(nonBillableHours(emp)) }}h</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Daily tasks view (today's digital log, emphasising James Hinsperger) -->
        <section
          v-else-if="activeSection === 'nonDigital'"
          class="space-y-4"
        >
          <div class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900 mb-1">
              Daily Tasks – Digital Activity Log
            </h3>
            <p class="text-xs text-gray-500">
              Shows what each person has done today, including bridge modeling, RFP work, email and
              Teams time, and admin entries. Data is mocked to mirror the v0 demo.
            </p>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <article
              v-for="summary in todaySummaries"
              :key="summary.employee.id"
              class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-5 space-y-3 shadow-xl"
            >
              <header class="flex items-center justify-between">
                <div>
                  <h4 class="text-sm font-semibold text-gray-900">
                    {{ summary.employee.name }}
                  </h4>
                  <p class="text-[11px] text-gray-500">
                    {{ summary.employee.role }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-[11px] text-gray-500">
                    Today
                  </p>
                  <p class="text-lg font-semibold text-gray-900">
                    {{ (summary.totalMinutes / 60).toFixed(1) }}h
                  </p>
                </div>
              </header>

              <div class="space-y-1 text-[11px]">
                <div
                  v-for="app in summary.apps"
                  :key="app.name"
                  class="flex items-center justify-between"
                >
                  <span class="text-gray-500">
                    {{ app.name }}
                  </span>
                  <span class="text-gray-900">
                    {{ (app.minutes / 60).toFixed(1) }}h
                  </span>
                </div>
              </div>

              <!-- Detailed list for James Hinsperger so the bridge + RFP work is visible -->
              <div
                v-if="summary.employee.id === 'emp11'"
                class="mt-3 border-t border-gray-200 pt-3 space-y-2 text-[11px]"
              >
                <p class="font-semibold text-gray-900">
                  Detailed timeline (bridge design & RFP work)
                </p>
                <div
                  v-for="event in summary.events"
                  :key="event.startTime"
                  class="flex items-start justify-between"
                >
                  <div class="w-2/5 text-gray-500">
                    {{
                      new Date(event.startTime).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}
                    –
                    {{
                      new Date(event.endTime).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}
                  </div>
                  <div class="w-3/5 text-gray-900">
                    <div class="font-medium">
                      {{ event.task }}
                    </div>
                    <div class="text-gray-500">
                      {{ event.subtask }}
                      <span class="ml-1">({{ event.app }})</span>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>

        <!-- Placeholder sections for Employee Insights, Non-digital Tasks, Settings -->
        <section
          v-else
          class="text-sm text-gray-500"
        >
          This section will mirror the corresponding v0 page. Core Employees / Projects / Project
          Insights functionality is already available above.
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { employees, type Employee } from '~/data/employees'
import { timeEvents, timeProjects, type TimeEvent, type TimeProject } from '~/data/timeTracking'
import { projectInsights } from '~/data/projectInsights'
import EmployeeCard from '~/components/EmployeeCard.vue'
import TimeScaleToggle from '~/components/TimeScaleToggle.vue'

type TimeScale = 'weekly' | 'monthly' | 'yearly'

const timeScale = ref<TimeScale>('weekly')
const searchQuery = ref('')
const selectedEmployeeId = ref<string | null>(null)
const activeSection = ref<'employees' | 'projects' | 'projectInsights' | 'employeeInsights' | 'nonDigital' | 'settings'>('employees')

const navItems = [
  { id: 'employees', label: 'Employees', icon: '👤' },
  { id: 'projects', label: 'Projects', icon: '📁' },
  { id: 'projectInsights', label: 'Project Insights', icon: '📈' },
  { id: 'employeeInsights', label: 'Employee Insights', icon: '📊' },
  { id: 'nonDigital', label: 'Daily Tasks', icon: '📝' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
] as const

const headerTitle = computed(() => {
  switch (activeSection.value) {
    case 'projects':
      return 'Projects Overview'
    case 'projectInsights':
      return 'Project Insights'
    case 'employeeInsights':
      return 'Employee Insights'
    case 'nonDigital':
      return 'Non-digital Tasks'
    case 'settings':
      return 'Settings'
    default:
      return 'Employee Productivity Dashboard'
  }
})

const headerSubtitle = computed(() => {
  switch (activeSection.value) {
    case 'projects':
      return 'Project-centric view for project managers'
    case 'projectInsights':
      return 'Aggregate performance across all projects'
    case 'employeeInsights':
      return 'Compare employee strengths and identify skill gaps'
    case 'nonDigital':
      return 'Manual / offline activities that are not captured digitally'
    case 'settings':
      return 'Configure tracking and visualization options'
    default:
      return 'Time tracking overview for all team members'
  }
})

const filteredEmployees = computed(() => {
  const query = searchQuery.value.toLowerCase()
  return employees.filter(
    (emp) =>
      emp.name.toLowerCase().includes(query) ||
      emp.role.toLowerCase().includes(query),
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
      .filter(
        (e) =>
          e.employeeId === selectedEmployeeId.value &&
          e.project &&
          e.project !== 'Admin' &&
          e.project !== 'Unknown',
      )
      .map((e) => e.project),
  )
  return timeProjects.filter((p) => employeeProjects.has(p.id))
})

// Helpers for employee insights (billable vs non-billable)
function billableHours(emp: Employee): number {
  if (emp.yearlyBreakdown) {
    const billable = emp.yearlyBreakdown.find((b) => b.name === 'Billable')
    return billable ? billable.value : (emp.yearlyHours || emp.weeklyHours * 52) * 0.85
  }
  return (emp.yearlyHours || emp.weeklyHours * 52) * 0.85
}

function nonBillableHours(emp: Employee): number {
  const total = emp.yearlyHours || emp.weeklyHours * 52
  return total - billableHours(emp)
}

function billableRatio(emp: Employee): number {
  const total = emp.yearlyHours || emp.weeklyHours * 52
  if (!total) return 0.8
  return billableHours(emp) / total
}

// Daily tasks / today summaries
const todayDate = '2025-12-15'

const todaySummaries = computed(() => {
  const todaysEvents = timeEvents.filter((e) => e.timestamp.startsWith(todayDate))

  const byEmployee: Record<
    string,
    {
      employee: Employee
      totalMinutes: number
      apps: { name: string; minutes: number }[]
      events: TimeEvent[]
    }
  > = {}

  todaysEvents.forEach((event) => {
    const emp = employees.find((e) => e.id === event.employeeId)
    if (!emp) return

    if (!byEmployee[event.employeeId]) {
      byEmployee[event.employeeId] = {
        employee: emp,
        totalMinutes: 0,
        apps: [],
        events: [],
      }
    }
    const entry = byEmployee[event.employeeId]
    entry.totalMinutes += event.duration
    entry.events.push(event)

    const appKey = event.app
    const app = entry.apps.find((a) => a.name === appKey)
    if (app) {
      app.minutes += event.duration
    } else {
      entry.apps.push({ name: appKey, minutes: event.duration })
    }
  })

  // Sort so James appears first if present
  return Object.values(byEmployee).sort((a, b) => {
    if (a.employee.id === 'emp11') return -1
    if (b.employee.id === 'emp11') return 1
    return b.totalMinutes - a.totalMinutes
  })
})

function handleEmployeeClick(emp: Employee) {
  selectedEmployeeId.value = emp.id === selectedEmployeeId.value ? null : emp.id
}

function handleNavClick(sectionId: (typeof navItems)[number]['id']) {
  activeSection.value = sectionId
  // Reset selection when leaving Employees section
  if (sectionId !== 'employees') {
    selectedEmployeeId.value = null
  }
}

function statusClass(status: 'On Track' | 'At Risk' | 'Behind') {
  if (status === 'On Track') {
    return 'bg-emerald-500/15 text-emerald-400'
  }
  if (status === 'At Risk') {
    return 'bg-amber-500/15 text-amber-400'
  }
  return 'bg-rose-500/15 text-rose-400'
}
</script>