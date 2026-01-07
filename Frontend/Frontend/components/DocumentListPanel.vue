<template>
  <!-- Backdrop -->
  <transition name="doc-fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
      @click="$emit('close')"
    ></div>
  </transition>

  <!-- Drawer -->
  <transition name="doc-slide">
    <aside
      v-if="isOpen"
      class="fixed z-50 top-16 bottom-4 right-4 w-full max-w-[440px] md:max-w-[32vw] min-w-[320px] bg-[#0b0c12]/98 border border-white/10 rounded-2xl shadow-[0_22px_70px_rgba(0,0,0,0.6)] overflow-hidden flex flex-col"
    >
      <header class="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-white/5 backdrop-blur">
        <div class="space-y-1">
          <p class="text-[11px] uppercase tracking-[0.22em] text-white/50">Models & Docs</p>
          <h3 class="text-lg font-semibold text-white">{{ title || 'Models & Documents' }}</h3>
          <p v-if="subtitle" class="text-xs text-white/60">{{ subtitle }}</p>
        </div>
        <button
          @click="$emit('close')"
          class="h-9 w-9 rounded-full bg-white/5 border border-white/10 text-white/80 hover:text-white hover:bg-white/10 transition flex items-center justify-center"
          title="Close"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-4 custom-scroll space-y-3">
        <div v-if="loading" class="space-y-3">
          <div v-for="i in 4" :key="i" class="animate-pulse rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
            <div class="h-4 w-32 bg-white/15 rounded"></div>
            <div class="h-3 w-3/4 bg-white/10 rounded"></div>
            <div class="flex gap-2">
              <div class="h-6 w-16 bg-white/10 rounded-full"></div>
              <div class="h-6 w-20 bg-white/10 rounded-full"></div>
            </div>
          </div>
        </div>

        <div v-else-if="documents.length === 0" class="flex flex-col items-center justify-center text-center py-12 gap-3 border border-dashed border-white/15 rounded-2xl bg-white/5">
          <div class="h-12 w-12 rounded-2xl bg-white/10 flex items-center justify-center border border-white/10">
            <svg class="w-6 h-6 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="space-y-1">
            <p class="text-white font-semibold text-sm">No models or documents yet</p>
            <p class="text-white/60 text-xs">Ask Sid to fetch 3D models or related docs to see them here.</p>
          </div>
        </div>

        <div v-else class="space-y-3">
          <p class="text-[11px] uppercase tracking-[0.16em] text-white/50 px-1">Available</p>
          <div
            v-for="(doc, index) in documents"
            :key="doc.id || index"
            @click="selectDocument(doc)"
            class="p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-purple-400/60 transition shadow-[0_10px_30px_rgba(0,0,0,0.35)] cursor-pointer"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 w-11 h-11 bg-gradient-to-br from-purple-600 to-fuchsia-600 rounded-xl flex items-center justify-center shadow-lg border border-white/15">
                <svg v-if="doc.metadata?.projectId && doc.metadata?.modelId" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <svg v-else class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0 space-y-1">
                <div class="flex items-center justify-between gap-2">
                  <h4 class="font-semibold text-white truncate">{{ doc.title || doc.name || 'Untitled' }}</h4>
                  <span
                    v-if="doc.metadata?.projectName"
                    class="text-[11px] px-2 py-1 rounded-full bg-white/10 border border-white/10 text-white/70 truncate"
                  >
                    {{ doc.metadata.projectName }}
                  </span>
                </div>
                <p v-if="doc.description" class="text-sm text-white/70 line-clamp-2">{{ doc.description }}</p>
                <div class="flex flex-wrap gap-2 pt-1">
                  <span
                    v-if="doc.metadata?.projectKey"
                    class="text-[11px] px-2 py-1 bg-purple-900/40 border border-purple-500/50 text-purple-100 rounded-full"
                  >
                    {{ doc.metadata.projectKey }}
                  </span>
                  <span
                    v-if="doc.metadata?.modelId"
                    class="text-[11px] px-2 py-1 bg-white/10 border border-white/15 text-white/70 rounded-full"
                  >
                    Model: {{ doc.metadata.modelId }}
                  </span>
                  <span
                    v-if="doc.reason"
                    class="text-[11px] px-2 py-1 bg-white/10 border border-white/15 text-white/70 rounded-full"
                  >
                    {{ doc.reason }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  </transition>

  <!-- Floating Action Button -->
  <button
    class="fixed bottom-6 right-6 z-50 h-12 rounded-2xl px-4 gap-3 flex items-center shadow-[0_12px_30px_rgba(0,0,0,0.4)] text-white font-semibold transition-all"
    :class="isOpen ? 'bg-gradient-to-r from-purple-500 to-fuchsia-600 ring-2 ring-purple-400/40' : 'bg-gradient-to-r from-purple-600 to-fuchsia-700 hover:brightness-110'"
    @click="isOpen ? $emit('close') : $emit('open')"
  >
    <div class="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center border border-white/15">
      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    </div>
    <span class="hidden sm:inline text-sm">Models & Docs</span>
  </button>
</template>

<script setup lang="ts">
interface Document {
  id: string
  title?: string
  name?: string
  description?: string
  url?: string
  filePath?: string
  metadata?: Record<string, string | number | undefined>
  reason?: string
}

interface Props {
  isOpen: boolean
  title?: string
  subtitle?: string
  documents: Document[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  title: 'Models & Documents',
  documents: () => [],
  loading: false
})

const emit = defineEmits<{
  close: []
  open: []
  'select-document': [document: Document]
}>()

function selectDocument(doc: Document) {
  emit('select-document', doc)
}
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar {
  width: 8px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.04);
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 8px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

.doc-slide-enter-active,
.doc-slide-leave-active {
  transition: transform 0.28s ease, opacity 0.28s ease;
}
.doc-slide-enter-from,
.doc-slide-leave-to {
  transform: translateX(110%);
  opacity: 0;
}
.doc-fade-enter-active,
.doc-fade-leave-active {
  transition: opacity 0.25s ease;
}
.doc-fade-enter-from,
.doc-fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  aside {
    right: 12px;
    left: 12px;
    max-width: none;
    min-width: 0;
  }
}
</style>
