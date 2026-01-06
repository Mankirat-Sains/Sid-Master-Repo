<template>
  <div class="h-full w-full bg-[#0f0f0f] text-white overflow-y-auto settings-view">
    <div class="max-w-4xl mx-auto px-6 py-6 space-y-5">
      <header class="mb-2">
        <h1 class="text-2xl font-semibold text-white">Settings</h1>
        <p class="text-sm text-white/60">Personalize Sidian to your workflow.</p>
      </header>

      <!-- Account -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">Account</p>
            <p class="card-sub">Manage your profile and access.</p>
          </div>
          <button class="btn-secondary" @click="handleLogout">Log out</button>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div>
            <p class="label">Name</p>
            <p class="value">{{ settings.account.name }}</p>
          </div>
          <div>
            <p class="label">Email</p>
            <p class="value">{{ settings.account.email }}</p>
          </div>
          <div class="sm:col-span-2 flex items-center justify-between gap-3">
            <div>
              <p class="label">Plan</p>
              <p class="value">{{ settings.account.plan }}</p>
            </div>
            <button class="btn-primary" @click="handleUpgrade">Upgrade</button>
          </div>
        </div>
      </section>

      <!-- Appearance -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">Appearance</p>
            <p class="card-sub">Theme and layout preferences.</p>
          </div>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div>
            <p class="label">Theme</p>
            <select v-model="settings.appearance.theme" class="input">
              <option value="dark">Dark (default)</option>
              <option value="system">System</option>
            </select>
          </div>
          <div>
            <p class="label">Accent color</p>
            <input
              v-model="settings.appearance.accent"
              type="color"
              class="w-full h-10 rounded border border-white/10 bg-[#111] cursor-pointer"
            />
          </div>
          <div>
            <p class="label">Density</p>
            <div class="flex gap-3">
              <label class="chip">
                <input type="radio" value="comfortable" v-model="settings.appearance.density" />
                <span>Comfortable</span>
              </label>
              <label class="chip">
                <input type="radio" value="compact" v-model="settings.appearance.density" />
                <span>Compact</span>
              </label>
            </div>
          </div>
          <div>
            <p class="label">Font size</p>
            <select v-model="settings.appearance.fontSize" class="input">
              <option value="sm">Small</option>
              <option value="md">Medium</option>
              <option value="lg">Large</option>
            </select>
          </div>
        </div>
      </section>

      <!-- AI and Chat -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">AI & Chat</p>
            <p class="card-sub">Control defaults for chat sessions.</p>
          </div>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div>
            <p class="label">Default model</p>
            <select v-model="settings.ai.model" class="input">
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <p class="label">Temperature ({{ settings.ai.temperature.toFixed(2) }})</p>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              v-model.number="settings.ai.temperature"
              class="range"
            />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">Conversation memory</p>
              <p class="text-xs text-white/50">When on, chat remembers context.</p>
            </div>
            <input type="checkbox" v-model="settings.ai.memory" class="toggle" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">Auto-title chats</p>
              <p class="text-xs text-white/50">Generate titles after responses.</p>
            </div>
            <input type="checkbox" v-model="settings.ai.autoTitle" class="toggle" />
          </div>
          <div class="sm:col-span-2 flex justify-end">
            <button class="btn-danger" @click="confirmClearMemory">Clear memory</button>
          </div>
        </div>
      </section>

      <!-- Workspace -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">Workspace</p>
            <p class="card-sub">Default navigation and safety.</p>
          </div>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div>
            <p class="label">Default landing</p>
            <select v-model="settings.workspace.landing" class="input">
              <option value="home">Chat</option>
              <option value="work">Work</option>
              <option value="timesheet">Timesheet</option>
              <option value="todo">To-Do</option>
              <option value="discussion">Discussion</option>
              <option value="settings">Settings</option>
            </select>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">Hover menus</p>
              <p class="text-xs text-white/50">Show submenus on hover.</p>
            </div>
            <input type="checkbox" v-model="settings.workspace.hoverMenus" class="toggle" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">Confirm before delete</p>
              <p class="text-xs text-white/50">Ask before destructive actions.</p>
            </div>
            <input type="checkbox" v-model="settings.workspace.confirmDelete" class="toggle" />
          </div>
        </div>
      </section>

      <!-- Notifications -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">Notifications</p>
            <p class="card-sub">Control delivery channels.</p>
          </div>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div class="flex items-center justify-between">
            <div>
              <p class="label">In-app</p>
            </div>
            <input type="checkbox" v-model="settings.notifications.inApp" class="toggle" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">Email</p>
            </div>
            <input type="checkbox" v-model="settings.notifications.email" class="toggle" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="label">System alerts</p>
            </div>
            <input type="checkbox" v-model="settings.notifications.system" class="toggle" />
          </div>
        </div>
      </section>

      <!-- Privacy -->
      <section class="card">
        <div class="card-head">
          <div>
            <p class="card-title">Privacy & Data</p>
            <p class="card-sub">Retention and exports.</p>
          </div>
        </div>
        <div class="card-body grid gap-4 sm:grid-cols-2">
          <div>
            <p class="label">Data retention</p>
            <select v-model="settings.privacy.retention" class="input">
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="365">365 days</option>
              <option value="forever">Keep until deleted</option>
            </select>
          </div>
          <div class="flex items-center justify-end gap-3 sm:col-span-2">
            <button class="btn-secondary" @click="handleExport">Export conversations</button>
            <button class="btn-danger" @click="confirmDeleteAll">Delete all conversations</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, watch } from 'vue'

type SettingsState = {
  account: {
    name: string
    email: string
    plan: string
  }
  appearance: {
    theme: 'dark' | 'system'
    accent: string
    density: 'comfortable' | 'compact'
    fontSize: 'sm' | 'md' | 'lg'
  }
  ai: {
    model: 'gpt-4o' | 'gpt-4o-mini' | 'custom'
    temperature: number
    memory: boolean
    autoTitle: boolean
  }
  workspace: {
    landing: 'home' | 'work' | 'timesheet' | 'todo' | 'discussion' | 'settings'
    hoverMenus: boolean
    confirmDelete: boolean
  }
  notifications: {
    inApp: boolean
    email: boolean
    system: boolean
  }
  privacy: {
    retention: '30' | '90' | '365' | 'forever'
  }
}

const STORAGE_KEY = 'settings-preferences-v1'

const settings = reactive<SettingsState>({
  account: {
    name: 'Alex Engineer',
    email: 'alex@example.com',
    plan: 'Pro'
  },
  appearance: {
    theme: 'dark',
    accent: '#7c3aed',
    density: 'comfortable',
    fontSize: 'md'
  },
  ai: {
    model: 'gpt-4o',
    temperature: 0.2,
    memory: true,
    autoTitle: true
  },
  workspace: {
    landing: 'home',
    hoverMenus: true,
    confirmDelete: true
  },
  notifications: {
    inApp: true,
    email: false,
    system: true
  },
  privacy: {
    retention: '90'
  }
})

function persist() {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (err) {
    console.warn('Unable to save settings', err)
  }
}

function load() {
  if (typeof window === 'undefined') return
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    const parsed = JSON.parse(raw) as Partial<SettingsState>
    if (parsed.account) Object.assign(settings.account, parsed.account)
    if (parsed.appearance) Object.assign(settings.appearance, parsed.appearance)
    if (parsed.ai) Object.assign(settings.ai, parsed.ai)
    if (parsed.workspace) Object.assign(settings.workspace, parsed.workspace)
    if (parsed.notifications) Object.assign(settings.notifications, parsed.notifications)
    if (parsed.privacy) Object.assign(settings.privacy, parsed.privacy)
  } catch (err) {
    console.warn('Unable to load settings', err)
  }
}

function handleLogout() {
  if (settings.workspace.confirmDelete && !confirm('Log out of Sidian?')) return
  alert('Logged out (stub).')
}

function handleUpgrade() {
  alert('Upgrade flow coming soon.')
}

function confirmClearMemory() {
  if (settings.workspace.confirmDelete && !confirm('Clear AI memory?')) return
  alert('Memory cleared.')
}

function handleExport() {
  alert('Export started (stub).')
}

function confirmDeleteAll() {
  if (settings.workspace.confirmDelete && !confirm('Delete all conversations? This cannot be undone.')) return
  alert('All conversations deleted (stub).')
}

onMounted(() => {
  load()
})

watch(
  () => settings,
  () => persist(),
  { deep: true }
)
</script>

<style scoped>
.card {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 16px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-title {
  font-weight: 600;
  color: #fff;
}
.card-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}
.card-body {
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
}
.label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}
.value {
  font-weight: 600;
  color: #fff;
}
.input {
  width: 100%;
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 10px;
  padding: 8px 10px;
}
.input:focus {
  outline: none;
  border-color: rgba(124, 58, 237, 0.6);
}
.toggle {
  width: 38px;
  height: 20px;
  accent-color: #7c3aed;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #0f0f0f;
  cursor: pointer;
}
.chip input {
  accent-color: #7c3aed;
}
.btn-primary {
  background: #7c3aed;
  color: #fff;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.btn-secondary {
  background: #161616;
  color: #fff;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
}
.btn-danger {
  background: #2d0f0f;
  color: #fca5a5;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(252, 165, 165, 0.3);
}
.range {
  width: 100%;
  accent-color: #7c3aed;
}
</style>
