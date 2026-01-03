<template>
  <div class="h-full w-full flex flex-col bg-foundation">
    <!-- Header -->
    <div class="border-b border-foundation-line bg-foundation-2 p-4">
      <div>
        <h2 class="text-xl font-semibold">Document Intelligence (RAG)</h2>
        <p class="text-sm text-foreground-muted">
          Query PDFs and technical drawings using AI
        </p>
      </div>
    </div>

    <!-- Main Content: Chat Interface -->
    <div class="flex-1 overflow-hidden">
      <DocumentChatInterface />
    </div>
  </div>
</template>

<script setup lang="ts">
const DocumentChatInterface = defineAsyncComponent(() => import('~/components/DocumentChatInterface.vue'))
</script>

