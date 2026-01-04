<template>
  <div>
    <HeaderNavBar />
    <div class="h-dvh w-dvh overflow-hidden flex flex-col">
      <!-- Static Spacer to allow for absolutely positioned HeaderNavBar  -->
      <div class="h-12 w-full shrink-0"></div>

      <div class="relative flex h-[calc(100dvh-3rem)]">
        <!-- Draggable Sidebar Container -->
        <div
          ref="sidebarContainer"
          :style="{ width: sidebarWidth + 'px' }"
          class="h-full shrink-0 relative border-r border-outline-3 overflow-hidden"
        >
          <DashboardProjectsSidebar />

          <!-- Resizer Handle -->
          <div
            ref="resizerHandle"
            class="absolute right-0 top-0 h-full w-1 cursor-ew-resize hover:bg-primary transition-colors z-20 group"
            @mousedown="startResize"
          >
            <div
              class="absolute inset-y-0 left-1/2 w-0.5 bg-outline-3 group-hover:bg-primary transition-colors"
            ></div>
          </div>
        </div>

        <main
          class="flex-1 h-full overflow-y-auto simple-scrollbar pt-4 lg:pt-6 pb-16"
          :style="{ width: `calc(100% - ${sidebarWidth}px)` }"
        >
          <div class="container mx-auto px-6 md:px-8">
            <slot />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
// Import the new component
import DashboardProjectsSidebar from '~/components/dashboard/ProjectsSidebar.vue'

const sidebarContainer = ref<HTMLElement | null>(null)
const resizerHandle = ref<HTMLElement | null>(null)

const minWidth = 200
const maxWidth = 600
const defaultWidth = 280

const sidebarWidth = ref(defaultWidth)
const isResizing = ref(false)

const startResize = (e: MouseEvent) => {
  isResizing.value = true
  document.addEventListener('mousemove', resize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
}

const resize = (e: MouseEvent) => {
  if (!isResizing.value || !sidebarContainer.value) return

  let newWidth = e.clientX
  if (newWidth < minWidth) newWidth = minWidth
  if (newWidth > maxWidth) newWidth = maxWidth
  sidebarWidth.value = newWidth
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', resize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''

  // Save width to localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('sidebarWidth', sidebarWidth.value.toString())
  }
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    const savedWidth = localStorage.getItem('sidebarWidth')
    if (savedWidth) {
      const width = parseInt(savedWidth)
      if (width >= minWidth && width <= maxWidth) {
        sidebarWidth.value = width
      }
    }
  }
})

onBeforeUnmount(() => {
  stopResize()
})
</script>
