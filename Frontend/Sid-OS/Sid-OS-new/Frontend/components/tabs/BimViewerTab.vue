<template>
  <div class="h-full w-full flex flex-col bg-foundation">
    <!-- Split Layout: Chat + Viewer -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Chat Panel (Left) -->
      <div
        class="flex flex-col border-r border-foundation-line bg-foundation transition-all duration-300"
        :class="viewerVisible ? 'w-96' : 'w-full'"
      >
        <ChatInterface
          @load-model="handleLoadModel"
          @toggle-viewer="toggleViewer"
          :viewer-visible="viewerVisible"
        />
      </div>

      <!-- Viewer Panel (Right) -->
      <div
        v-if="viewerVisible"
        class="flex-1 relative border-l border-foundation-line bg-foundation transition-all duration-300"
      >
        <SpeckleViewer
          v-if="currentModel"
          :project-id="currentModel.projectId"
          :model-id="currentModel.modelId"
          :commit-id="currentModel.commitId"
          :project-name="currentModel.projectName"
          @close="closeViewer"
        />
        <div
          v-else
          class="flex h-full items-center justify-center text-foreground-muted"
        >
          <div class="text-center">
            <p class="text-lg mb-2">No model loaded</p>
            <p class="text-sm">
              Ask about a project to view its BIM model
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ModelInfo {
  projectId: string
  modelId: string
  commitId?: string
  projectNumber?: string
  projectName?: string
}

const currentModel = ref<ModelInfo | null>(null)
const viewerVisible = ref(false)

function handleLoadModel(model: ModelInfo) {
  currentModel.value = model
  viewerVisible.value = true
}

function toggleViewer() {
  viewerVisible.value = !viewerVisible.value
}

function closeViewer() {
  viewerVisible.value = false
  currentModel.value = null
}
</script>

