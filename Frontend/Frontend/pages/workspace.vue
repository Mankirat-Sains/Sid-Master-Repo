<template>
  <div class="min-h-screen bg-black text-white flex flex-col">
    <!-- Header -->
    <header class="h-11 flex items-center justify-between px-4 border-b border-white/10 bg-black">
      <div class="flex items-center gap-2">
        <div class="h-7 w-7 rounded bg-red-600 flex items-center justify-center text-xs font-bold" aria-label="Navier AI logo">N</div>
        <span class="text-sm font-semibold">Navier AI</span>
      </div>
      <div class="flex items-center gap-3">
        <div class="h-8 w-8 rounded-full bg-white/10 border border-white/10"></div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Icon rail -->
      <aside class="w-16 bg-[#0b0b0b] border-r border-white/10 flex flex-col items-center py-3 space-y-2">
        <button
          v-for="icon in railIcons"
          :key="icon.id"
          class="relative h-10 w-10 rounded border border-transparent flex items-center justify-center text-white/60 hover:text-white hover:border-white/10 transition"
          :aria-label="icon.label"
        >
          <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-red-600 rounded-r" v-if="icon.id === 'home'"></span>
          <component :is="icon.component" class="w-5 h-5" />
        </button>
        <div class="mt-auto h-10 w-10 rounded border border-white/10 bg-white/5"></div>
      </aside>

      <!-- Conversation list -->
      <aside class="w-72 bg-[#0d0d0d] border-r border-white/10 flex flex-col">
        <div class="flex items-center gap-2 px-3 py-3 border-b border-white/10">
          <button class="h-9 px-3 rounded bg-white/8 border border-white/12 text-xs font-semibold hover:bg-white/12 transition flex items-center gap-2">
            <span class="text-sm">*</span>
          </button>
          <button class="flex-1 h-9 px-3 rounded bg-white/8 border border-white/12 text-xs font-semibold hover:bg-white/12 transition text-left">
            + NEW AGENT
          </button>
        </div>

        <div class="px-3 py-3 border-b border-white/10">
          <div class="relative">
            <input
              v-model="search"
              type="text"
              class="w-full rounded bg-white/5 border border-white/10 text-sm px-3 py-2 placeholder-white/40 focus:outline-none focus:border-white/30"
              placeholder="Search agents..."
              aria-label="Search agents"
            />
            <svg class="absolute right-3 top-2.5 w-4 h-4 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scroll">
          <div
            v-for="section in conversationSections"
            :key="section.title"
            class="px-3 py-3"
          >
            <p class="text-[11px] uppercase tracking-[0.2em] text-white/35 mb-2">{{ section.title }}</p>
            <div class="space-y-1.5">
              <button
                v-for="conv in section.items"
                :key="conv.id"
                class="w-full text-left px-3 py-2 rounded bg-transparent border border-transparent hover:bg-white/5 transition"
              >
                <p class="text-sm font-semibold truncate" :title="conv.title">{{ conv.title }}</p>
                <p class="text-[12px] text-white/55">{{ conv.time }}</p>
              </button>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 bg-black flex flex-col items-center justify-center px-6">
        <div class="flex flex-col items-center gap-2 mb-6">
          <div class="text-6xl font-light text-white/85">*</div>
          <p class="text-lg text-white/75">What can I help with?</p>
        </div>

        <div class="flex flex-col items-center gap-3 w-full max-w-5xl">
          <div class="flex items-center gap-2">
            <button
              v-for="tag in tags"
              :key="tag"
              class="px-3 py-1.5 rounded-full bg-[#2a2a2a] text-xs text-white/85 border border-[#3a3a3a]"
            >
              {{ tag }}
              <span class="ml-1 text-white/50">×</span>
            </button>
          </div>

          <div class="w-[85%] max-w-5xl rounded-lg bg-[#1f1f1f] border border-[#2e2e2e] shadow-[0_18px_60px_rgba(0,0,0,0.55)] overflow-hidden">
            <div class="px-6 py-5 space-y-3">
              <div class="flex items-center gap-3">
                <input
                  v-model="prompt"
                  type="text"
                  class="flex-1 bg-transparent text-white placeholder-white/60 text-[18px] font-medium focus:outline-none border-0 focus:ring-0"
                  placeholder="Setup a..."
                  aria-label="Prompt input"
                />
                <button class="h-11 w-11 rounded-sm bg-[#2a2a2a] border border-[#3a3a3a] text-white/70 hover:text-white transition flex items-center justify-center" aria-label="Attach">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.586-6.586a4 4 0 10-5.656-5.656L5.757 9.343" />
                  </svg>
                </button>
                <button class="h-11 w-11 bg-white text-black rounded-sm flex items-center justify-center hover:scale-105 transition" aria-label="Send">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
              <div class="flex items-center gap-2 text-sm text-white/75">
                <button class="px-3 py-2 rounded bg-[#2a2a2a] border border-[#3a3a3a] flex items-center gap-1">
                  <span>gpt-4o-120b</span>
                  <svg class="w-3 h-3 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

import { ref } from 'vue'
import FolderIcon from '~/components/icons/FolderIcon.vue'
import ChatIcon from '~/components/icons/ChatIcon.vue'
import GearIcon from '~/components/icons/GearIcon.vue'
import ClockIcon from '~/components/icons/ClockIcon.vue'

const railIcons = [
  { id: 'home', component: FolderIcon, label: 'Home' },
  { id: 'search', component: ChatIcon, label: 'Search' },
  { id: 'settings', component: GearIcon, label: 'Settings' },
  { id: 'history', component: ClockIcon, label: 'History' }
]

const search = ref('')
const prompt = ref('')
const tags = ['missile.ai']

const conversationSections = [
  {
    title: 'Today',
    items: [
      { id: 1, title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '52m ago' },
      { id: 2, title: 'CFD Simulation Setup Review', short: 'CFD Setup Review', time: '1h ago' },
      { id: 3, title: 'Calculating Reynolds number', short: 'Reynolds number', time: '2h ago' },
      { id: 4, title: 'CFD Mesh Creation Request', short: 'CFD Mesh Request', time: '2h ago' },
      { id: 5, title: 'Python Conversion: Knots to Mach', short: 'Knots to Mach', time: '3h ago' },
      { id: 6, title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '5h ago' },
      { id: 7, title: 'CFD Simulation for Car Model', short: 'Car CFD Sim', time: '6h ago' },
      { id: 8, title: 'Ahmed Body Mesh Generation', short: 'Ahmed Mesh Gen', time: '6h ago' }
    ]
  },
  {
    title: 'Yesterday',
    items: [
      { id: 9, title: 'CFD Simulation Request follow-up', short: 'CFD follow-up', time: 'Yesterday' }
    ]
  },
  {
    title: 'This Month',
    items: [
      { id: 10, title: 'Mesh Setup for Y+ Target', short: 'Y+ Target mesh', time: 'Nov 24' },
      { id: 11, title: 'Workspace Inquiry and Mapping', short: 'Workspace inquiry', time: 'Nov 24' },
      { id: 12, title: 'Available Tools Inquiry', short: 'Tools inquiry', time: 'Nov 19' },
      { id: 13, title: 'Mesh Setup for Geometry', short: 'Geometry mesh', time: 'Nov 19' },
      { id: 14, title: 'Mesh Refinement Zone Design', short: 'Refinement zone', time: 'Nov 19' }
    ]
  }
]
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar {
  width: 8px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: #0d0d0d;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: #1f1f1f;
  border-radius: 8px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: #2a2a2a;
}
</style>
