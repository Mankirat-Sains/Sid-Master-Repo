<!-- Example page showing how to use SkyCivViewer in a Nuxt app -->
<template>
  <div class="min-h-screen bg-gray-900 p-4">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold text-white mb-6">SkyCiv Structural Analysis Demo</h1>
      
      <div class="bg-[#1a1a1a] rounded-lg shadow-2xl">
        <SkyCivViewer height="700px" />
      </div>
      
      <div class="mt-6 text-gray-400 text-sm">
        <p>This demo loads SkyCiv structural models and runs analysis via the SkyCiv API.</p>
        <p class="mt-2">Select a model from the dropdown and click "Run Analysis" to visualize the structure.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// This is an example - copy SkyCivViewer.vue to your components directory
// and import it like this:
// import SkyCivViewer from '~/components/SkyCivViewer.vue'
</script>

