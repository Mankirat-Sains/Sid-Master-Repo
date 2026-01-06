<template>
  <div class="h-full bg-[#0f0f0f] text-white overflow-y-auto todo-view">
    <div class="max-w-4xl mx-auto px-6 py-6 space-y-5">
      <header class="space-y-1">
        <p class="text-xs uppercase tracking-[0.2em] text-white/50">Tasks</p>
        <h1 class="text-2xl font-semibold">To-Do List</h1>
        <p class="text-sm text-white/65">Focus on what's next, keep it lean.</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <section class="card">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-semibold">Today</h2>
            <span class="text-xs text-white/60">{{ todayTasks.length }} items</span>
          </div>
          <div class="space-y-2">
            <div
              v-for="task in todayTasks"
              :key="task.title"
              class="card-row"
            >
              <div>
                <p class="font-semibold text-white">{{ task.title }}</p>
                <p class="text-xs text-white/60">{{ task.note }}</p>
              </div>
              <span :class="['badge', statusClass(task.status)]">{{ task.status }}</span>
            </div>
          </div>
        </section>

        <section class="card">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-semibold">Backlog</h2>
            <span class="text-xs text-white/60">{{ backlogTasks.length }} queued</span>
          </div>
          <div class="space-y-2">
            <div
              v-for="task in backlogTasks"
              :key="task.title"
              class="card-row"
            >
              <div>
                <p class="font-semibold text-white">{{ task.title }}</p>
                <p class="text-xs text-white/60">{{ task.note }}</p>
              </div>
              <div class="flex gap-2 items-center">
                <span class="pill">{{ task.tag }}</span>
                <span :class="['badge', statusClass(task.status)]">{{ task.status }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="card">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h3 class="text-lg font-semibold">Quick Capture</h3>
            <p class="text-xs text-white/60">Drop ideas here; they'll sync with Sid.</p>
          </div>
          <button class="btn">Add task</button>
        </div>
        <div class="space-y-2">
          <input
            type="text"
            placeholder="Task title"
            class="input"
          />
          <textarea
            rows="3"
            placeholder="Details"
            class="input resize-none"
          />
        </div>
      </section>

      <p class="text-center text-xs text-white/40">Coming soon: deeper integrations and reminders.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
type Status = 'todo' | 'in-progress' | 'done'

const todayTasks: { title: string; note: string; status: Status }[] = [
  { title: 'Review structural calcs', note: 'Double-check live load assumptions', status: 'in-progress' },
  { title: 'Send client update', note: 'Share revised model snapshot', status: 'todo' },
  { title: 'Prep QA/QC checklist', note: 'Bridge handoff this afternoon', status: 'done' }
]

const backlogTasks: { title: string; note: string; status: Status; tag: string }[] = [
  { title: 'Re-run CFD post-processing', note: 'Verify mesh refinement zones', status: 'todo', tag: 'Simulation' },
  { title: 'Draft RFP response', note: 'Include timeline and scope exclusions', status: 'in-progress', tag: 'Docs' },
  { title: 'Collect precedent projects', note: 'Find 3 analogs with similar span', status: 'todo', tag: 'Research' }
]

function statusClass(status: Status) {
  if (status === 'done') return 'badge-success'
  if (status === 'in-progress') return 'badge-warn'
  return 'badge-muted'
}
</script>

<style scoped>
.card {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}
.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}
.badge {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 11px;
  text-transform: capitalize;
}
.badge-success {
  background: rgba(124, 58, 237, 0.28);
  color: #e9d5ff;
  border-color: rgba(124, 58, 237, 0.45);
}
.badge-warn {
  background: rgba(124, 58, 237, 0.18);
  color: #d8b4fe;
  border-color: rgba(124, 58, 237, 0.35);
}
.badge-muted {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}
.pill {
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(124, 58, 237, 0.15);
  color: #c084fc;
  border: 1px solid rgba(124, 58, 237, 0.25);
  font-size: 11px;
}
.btn {
  background: rgba(124, 58, 237, 0.25);
  border: 1px solid rgba(124, 58, 237, 0.4);
  color: #e9d5ff;
  padding: 6px 12px;
  border-radius: 10px;
  font-weight: 600;
}
.input {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
  color: #fff;
}
.input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}
.input:focus {
  outline: none;
  border-color: rgba(124, 58, 237, 0.6);
}
</style>
