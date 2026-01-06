<template>
  <div class="h-full bg-[#0f0f0f] text-white overflow-y-auto discussion-view">
    <div class="max-w-5xl mx-auto px-6 py-6 space-y-5">
      <header class="space-y-1">
        <p class="text-xs uppercase tracking-[0.2em] text-white/50">Collaboration</p>
        <h1 class="text-2xl font-semibold">Discussion</h1>
        <p class="text-sm text-white/65">Recent threads across projects.</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <section class="card md:col-span-2">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-semibold">Active threads</h2>
            <button class="btn">New thread</button>
          </div>
          <div class="space-y-2">
            <article
              v-for="thread in threads"
              :key="thread.title"
              class="card-row"
            >
              <div class="space-y-1">
                <p class="font-semibold text-white">{{ thread.title }}</p>
                <p class="text-xs text-white/60">{{ thread.snippet }}</p>
                <div class="flex items-center gap-2">
                  <span class="pill">{{ thread.project }}</span>
                  <span class="text-xs text-white/50">{{ thread.updated }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs text-white/60">
                <span>{{ thread.participants }} ppl</span>
                <span>·</span>
                <span>{{ thread.messages }} msgs</span>
              </div>
            </article>
          </div>
        </section>

        <aside class="card space-y-3">
          <h3 class="text-lg font-semibold">Pinned</h3>
          <div v-for="pin in pinned" :key="pin.title" class="card-row">
            <div>
              <p class="font-semibold text-white">{{ pin.title }}</p>
              <p class="text-xs text-white/60">{{ pin.note }}</p>
            </div>
            <span class="pill">{{ pin.tag }}</span>
          </div>
        </aside>
      </div>

      <p class="text-center text-xs text-white/40">Coming soon: inline replies and file annotations.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const threads = [
  { title: 'CFD mesh changes', snippet: 'Updated refinement near intake; need approval.', project: 'Submarine Sim', updated: '5m ago', participants: 3, messages: 14 },
  { title: 'Bridge RFP scope', snippet: 'Confirm deliverables for week 2.', project: 'IA Analytics', updated: '18m ago', participants: 4, messages: 22 },
  { title: 'Model QA checklist', snippet: 'Tracking open QA items before sign-off.', project: 'Structural', updated: '1h ago', participants: 2, messages: 9 }
]

const pinned = [
  { title: 'Client review deck', note: 'Draft slides ready for comments.', tag: 'Deck' },
  { title: 'Data room links', note: 'All assets consolidated.', tag: 'Links' }
]
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
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
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
</style>
