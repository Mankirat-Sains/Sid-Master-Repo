<template>
  <div
    v-if="hasMetadata"
    class="mt-3 w-full rounded-xl border border-white/10 bg-white/5 text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]"
  >
    <button
      class="w-full flex items-center justify-between px-3 py-2 text-left text-sm font-semibold hover:bg-white/5 transition"
      @click="isExpanded = !isExpanded"
      :aria-expanded="isExpanded"
    >
      <span class="flex items-center gap-2">
        <span>🔍 Sources &amp; References</span>
        <span class="text-white/60 text-xs">
          ({{ docCount }} {{ docCount === 1 ? 'document' : 'documents' }})
        </span>
      </span>
      <span class="text-white/70 text-xs">{{ isExpanded ? '▲' : '▼' }}</span>
    </button>

    <div v-if="isExpanded" class="border-t border-white/10 divide-y divide-white/10">
      <div v-if="metadata?.documents?.length" class="px-3 py-3 space-y-2">
        <div class="text-xs font-semibold text-white/70 flex items-center gap-2">
          <span>📚 Retrieved Documents:</span>
        </div>
        <div
          v-for="(doc, idx) in metadata?.documents || []"
          :key="doc.source_id || idx"
          class="rounded-lg border border-white/10 bg-black/30 px-3 py-2 space-y-1"
        >
          <div class="flex items-center justify-between gap-2">
            <div class="text-sm font-semibold text-white">
              {{ idx + 1 }}. {{ doc.title || 'Source' }}
            </div>
            <div v-if="doc.relevance" class="text-[11px] text-white/70">
              Relevance: {{ formatRelevance(doc.relevance) }}
            </div>
          </div>
          <div v-if="doc.project" class="text-[11px] text-white/65">Project: {{ doc.project }}</div>
          <div v-if="doc.date" class="text-[11px] text-white/65">Date: {{ doc.date }}</div>
          <div v-if="doc.author" class="text-[11px] text-white/65">Author: {{ doc.author }}</div>
          <div v-if="doc.content_preview" class="text-[12px] text-white/80 leading-snug">
            {{ doc.content_preview }}
          </div>
          <div v-if="doc.source_id" class="text-[10px] text-white/50">ID: {{ doc.source_id }}</div>
        </div>
      </div>

      <div v-if="metadata?.warnings?.length" class="px-3 py-3 space-y-1">
        <div class="text-xs font-semibold text-amber-300 flex items-center gap-2">
          <span>⚠️ Documentation Status:</span>
        </div>
        <ul class="list-disc list-inside text-[12px] text-white/80 space-y-0.5">
          <li v-for="(warning, idx) in metadata.warnings" :key="idx">{{ warning }}</li>
        </ul>
      </div>

      <div v-if="metadata?.search_metadata" class="px-3 py-3 space-y-1 text-[12px] text-white/80">
        <div class="text-xs font-semibold text-white/80 flex items-center gap-2">
          <span>🔎 Search Query Details:</span>
        </div>
        <div v-if="metadata.search_metadata.original_query">
          Original Query: "{{ metadata.search_metadata.original_query }}"
        </div>
        <div v-if="metadata.search_metadata.expanded_queries?.length">
          Expanded Queries: "{{ metadata.search_metadata.expanded_queries.join('", "') }}"
        </div>
        <div v-if="metadata.search_metadata.support_score !== undefined && metadata.search_metadata.support_score !== null">
          Support Score: {{ Number(metadata.search_metadata.support_score).toFixed(2) }}/1.0
        </div>
        <div>Retrieved: {{ docCount }} relevant {{ docCount === 1 ? 'document' : 'documents' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Source {
  title?: string
  project?: string
  date?: string
  author?: string
  relevance?: number
  content_preview?: string
  source_id?: string
}

interface CitationsMetadata {
  documents?: Source[]
  warnings?: string[]
  search_metadata?: {
    original_query?: string
    expanded_queries?: string[]
    support_score?: number
  }
}

const props = defineProps<{
  metadata?: CitationsMetadata
}>()

const isExpanded = ref(false)
const docCount = computed(() => props.metadata?.documents?.length || 0)
const hasMetadata = computed(
  () =>
    !!props.metadata &&
    ((props.metadata.documents && props.metadata.documents.length > 0) ||
      (props.metadata.warnings && props.metadata.warnings.length > 0) ||
      props.metadata.search_metadata)
)

function formatRelevance(value: number | undefined) {
  if (value === undefined || value === null) return ''
  return `${Math.round((Number(value) || 0) * 100)}%`
}
</script>

<style scoped>
.sources-container {
  width: 100%;
}
.sources-toggle {
  font-family: inherit;
}
.source-card {
  transition: border-color 0.2s ease, background-color 0.2s ease;
}
.source-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background-color: rgba(255, 255, 255, 0.06);
}
</style>
