<template>
  <div class="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#050507] via-[#0b0f1a] to-[#0f0a1b] text-white">
    <div class="pointer-events-none absolute -left-48 -top-32 h-[28rem] w-[28rem] rounded-full bg-purple-700/25 blur-[140px]"></div>
    <div class="pointer-events-none absolute right-[-10rem] top-0 h-[32rem] w-[32rem] rounded-full bg-purple-500/18 blur-[150px]"></div>
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-black/35 via-transparent to-black/45"></div>
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.05),_transparent_42%)]"></div>

    <div class="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10 lg:px-10">
      <header class="mb-12 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-[0_15px_60px_rgba(0,0,0,0.35)]">
            <span class="text-lg font-semibold text-purple-200 drop-shadow">Sid</span>
          </div>
          <div>
            <p class="text-xl font-semibold">Sid</p>
            <p class="text-sm text-gray-300">Autonomous engineer</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="hidden rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-gray-200/80 transition hover:border-white/30 hover:text-white sm:inline-flex"
            @click="goToLogin"
          >
            View login
          </button>
          <button
            class="rounded-xl bg-gradient-to-r from-purple-500 to-purple-400 px-5 py-3 text-sm font-semibold text-black shadow-lg shadow-purple-900/50 transition hover:brightness-110"
            @click="goToLogin"
          >
            Launch Sid
          </button>
        </div>
      </header>

      <main class="grid items-center gap-12 lg:grid-cols-[1.05fr,0.95fr]">
        <div class="space-y-8">
          <p class="text-xs font-semibold uppercase tracking-[0.4em] text-purple-200/70">AI, but shipping</p>
          <h1 class="text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl drop-shadow-[0_8px_24px_rgba(0,0,0,0.35)]">
            Build faster with a sleek, autonomous engineer in your corner.
          </h1>
          <p class="max-w-2xl text-lg text-gray-200/90">
            Sid studies your stack, plans the work, and executes with you—keeping every decision visible, traceable, and ready to ship.
          </p>

          <div class="flex flex-wrap items-center gap-4">
            <button
              class="rounded-xl bg-white px-6 py-3 text-base font-semibold text-black transition hover:-translate-y-0.5 hover:shadow-xl"
              @click="goToLogin"
            >
              Start with login
            </button>
            <button
              class="rounded-xl border border-white/15 px-5 py-3 text-base font-semibold text-white transition hover:border-white/30 hover:-translate-y-0.5"
              @click="goToLogin"
            >
              See it live
            </button>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="feature in features"
              :key="feature.title"
              class="rounded-2xl border border-white/10 bg-[#0f1225]/80 p-4 backdrop-blur-md shadow-[0_12px_40px_rgba(0,0,0,0.35)]"
            >
              <p class="mb-2 text-sm font-semibold text-purple-200">{{ feature.title }}</p>
              <p class="text-sm text-gray-200/85">{{ feature.description }}</p>
            </div>
          </div>
        </div>

        <div class="relative">
          <div class="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-purple-500/18 via-transparent to-white/8 blur-2xl"></div>
          <div class="relative rounded-[2rem] border border-white/12 bg-[#0d1022]/85 p-6 shadow-[0_18px_90px_rgba(0,0,0,0.55)] backdrop-blur-xl">
            <div class="mb-6 flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-200/70">Now running</p>
                <p class="text-2xl font-semibold">Model: Sid / Studio</p>
              </div>
              <div class="rounded-xl bg-purple-500/20 px-4 py-2 text-sm font-semibold text-purple-100">Live</div>
            </div>

            <div class="mb-6 rounded-xl border border-white/12 bg-[#13162c]/90 p-4">
              <p class="text-sm text-gray-200/70">Next action</p>
              <p class="text-lg font-semibold text-white">Drafting solution plan for your repo</p>
              <p class="mt-2 text-sm text-gray-200/70">
                Pulling context, mapping services, and aligning milestones with your guidelines.
              </p>
            </div>

            <div class="grid gap-3 sm:grid-cols-3">
              <div class="rounded-xl border border-white/12 bg-[#0f1225]/85 p-4">
                <p class="text-xs uppercase tracking-wide text-gray-300/80">Confidence</p>
                <p class="text-3xl font-semibold text-white">92%</p>
              </div>
              <div class="rounded-xl border border-white/12 bg-[#0f1225]/85 p-4">
                <p class="text-xs uppercase tracking-wide text-gray-300/80">Time saved</p>
                <p class="text-3xl font-semibold text-white">18h</p>
              </div>
              <div class="rounded-xl border border-white/12 bg-[#0f1225]/85 p-4">
                <p class="text-xs uppercase tracking-wide text-gray-300/80">Reviews</p>
                <p class="text-3xl font-semibold text-white">Ready</p>
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

const features = [
  {
    title: 'Autonomous execution',
    description: 'Sid plans, codes, and tests across your stack without losing the thread.'
  },
  {
    title: 'Transparent workflow',
    description: 'Every milestone stays reviewable—diffs, logs, and decisions in one place.'
  },
  {
    title: 'Speed with control',
    description: 'Keep approvals where you want them while Sid accelerates the rest.'
  }
]

const goToLogin = () => navigateTo('/login')
</script>
