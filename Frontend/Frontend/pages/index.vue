<template>
  <div class="min-h-screen flex items-center justify-center bg-white text-gray-700">
    Redirecting to login...
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

await navigateTo('/login', { replace: true })
</script>
