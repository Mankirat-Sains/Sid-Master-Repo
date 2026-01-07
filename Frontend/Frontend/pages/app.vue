<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#04060d] via-[#090c1a] to-[#0d0820] text-white">
    <div class="text-center space-y-4">
      <div class="text-sm text-white/70">Redirecting to workspace...</div>
      <div class="h-10 w-10 mx-auto rounded-full border-2 border-purple-400/60 border-t-transparent animate-spin"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

await navigateTo('/workspace', { replace: true })
</script>
