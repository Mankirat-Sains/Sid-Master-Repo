<template>
  <div>
    <Portal to="navigation">
      <HeaderNavLink :to="projectsRoute" name="Projects" :separator="false" />
      <HeaderNavLink name="Files" :separator="false" />
    </Portal>

    <div class="max-w-7xl mx-auto py-8">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-heading-xl mb-2">All Files</h1>
          <p class="text-body-sm text-foreground-2">
            View all models and documents across your projects
          </p>
        </div>

        <!-- Filters -->
        <div class="flex items-center gap-4">
          <select
            v-model="selectedProjectFilter"
            class="px-3 py-2 rounded border border-outline-3 bg-foundation-2 text-foreground text-body-sm"
          >
            <option value="">All Projects</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>

          <select
            v-model="selectedTypeFilter"
            class="px-3 py-2 rounded border border-outline-3 bg-foundation-2 text-foreground text-body-sm"
          >
            <option value="">All Types</option>
            <option value="model">3D Models</option>
            <option value="pdf">PDFs</option>
          </select>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <Loader2 class="size-8 animate-spin text-foreground-2" />
      </div>

      <!-- Files Grid -->
      <div
        v-else-if="filteredFiles.length > 0"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        <div
          v-for="file in filteredFiles"
          :key="file.id"
          class="bg-foundation-2 rounded-lg p-4 hover:bg-foundation-3 transition-colors cursor-pointer border border-outline-3"
          @click="openFile(file)"
        >
          <div class="flex items-start gap-3 mb-3">
            <div
              class="flex-shrink-0 w-10 h-10 rounded flex items-center justify-center"
              :class="
                file.type === 'pdf'
                  ? 'bg-red-100 text-red-600'
                  : file.type === 'model'
                  ? 'bg-blue-100 text-blue-600'
                  : 'bg-foundation-3 text-foreground-2'
              "
            >
              <FileText v-if="file.type === 'pdf'" class="size-5" />
              <Box v-else class="size-5" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-body-sm font-medium truncate" :title="file.name">
                {{ file.name }}
              </h3>
              <p class="text-body-3xs text-foreground-2 mt-1">
                {{ file.projectName }}
              </p>
            </div>
          </div>
          <div
            class="flex items-center justify-between text-body-3xs text-foreground-3"
          >
            <span>{{ formatDate(file.createdAt) }}</span>
            <span v-if="file.type === 'pdf' && file.fileSize" class="uppercase">
              {{ formatFileSize(file.fileSize) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <Folder class="size-16 mx-auto mb-4 text-foreground-3" />
        <h3 class="text-heading-md mb-2">No files found</h3>
        <p class="text-body-sm text-foreground-2">
          {{
            selectedProjectFilter || selectedTypeFilter
              ? 'Try adjusting your filters'
              : 'Upload files to your projects to see them here'
          }}
        </p>
      </div>
    </div>

    <!-- File Preview Dialog -->
    <LayoutDialog
      v-model:open="showPreviewDialog"
      max-width="lg"
      :buttons="[{ text: 'Close', onClick: () => (showPreviewDialog = false) }]"
    >
      <template #header>
        {{ previewFile.value ? previewFile.value.name : 'File Preview' }}
      </template>
      <template v-if="previewFile.value">
        <div class="flex flex-col space-y-2 h-[600px]">
          <div v-if="previewError" class="flex justify-center items-center h-full">
            <span class="inline-flex space-x-2 items-center text-danger">
              {{ previewError }}
            </span>
          </div>
          <template v-else-if="previewFile.value.type === 'pdf' && previewUrl">
            <PdfViewer :url="previewUrl" />
          </template>
          <template v-else-if="previewFile.value.type === 'model'">
            <div class="flex justify-center items-center h-full">
              <NuxtLink
                :to="`/projects/${previewFile.value.projectId}/models/${previewFile.value.modelId}`"
                class="text-primary hover:text-primary-focus"
              >
                View in 3D Viewer →
              </NuxtLink>
            </div>
          </template>
          <template v-else>
            <div class="flex justify-center items-center h-full">
              <span class="text-body-sm text-foreground-2">Preview not available</span>
            </div>
          </template>
        </div>
      </template>
    </LayoutDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useQuery } from '@vue/apollo-composable'
import { projectsDashboardQuery } from '~~/lib/projects/graphql/queries'
import { projectsRoute } from '~/lib/common/helpers/route'
import { graphql } from '~~/lib/common/generated/gql'
import { useFileDownload } from '~~/lib/core/composables/fileUpload'
import { Folder, FileText, Box, Loader2 } from 'lucide-vue-next'
import PdfViewer from '~/components/file-viewers/PdfViewer.vue'
import dayjs from 'dayjs'
import { useRouter } from 'vue-router'

useHead({
  title: 'All Files'
})

definePageMeta({
  middleware: ['auth']
})

interface FileItem {
  id: string
  name: string
  type: 'model' | 'pdf'
  projectId: string
  projectName: string
  createdAt: string
  fileSize?: number
  modelId?: string
  blobId?: string
}

const allFilesQuery = graphql(`
  query AllFiles($cursor: String) {
    activeUser {
      projects(filter: { personalOnly: false }, limit: 100, cursor: $cursor) {
        items {
          id
          name
          models(limit: 100) {
            items {
              id
              name
              createdAt
            }
          }
        }
        cursor
        totalCount
      }
    }
  }
`)

const { result: projectsResult } = useQuery(projectsDashboardQuery, () => ({
  filter: {
    personalOnly: false
  },
  cursor: null
}))

const { result: allFilesResult, loading } = useQuery(allFilesQuery, () => ({
  cursor: null
}))

const { getBlobUrl } = useFileDownload()
const router = useRouter()

const selectedProjectFilter = ref('')
const selectedTypeFilter = ref('')
const showPreviewDialog = ref(false)
const previewFile = ref<FileItem | null>(null)
const previewUrl = ref<string | null>(null)
const previewError = ref<string | null>(null)

const projects = computed(() => {
  return projectsResult.value?.activeUser?.projects?.items || []
})

const allFiles = computed<FileItem[]>(() => {
  const items: FileItem[] = []
  const projectItems = allFilesResult.value?.activeUser?.projects?.items || []

  for (const project of projectItems) {
    // Add models
    for (const model of project.models?.items || []) {
      items.push({
        id: model.id,
        name: model.name,
        type: 'model',
        projectId: project.id,
        projectName: project.name,
        createdAt: model.createdAt,
        modelId: model.id
      })
    }

    // Note: PDFs would need to be fetched separately via file uploads or blobs
    // For now, we'll show models. PDFs can be added via a separate query
  }

  return items.sort((a, b) => {
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  })
})

const filteredFiles = computed(() => {
  let filtered = allFiles.value

  if (selectedProjectFilter.value) {
    filtered = filtered.filter((f) => f.projectId === selectedProjectFilter.value)
  }

  if (selectedTypeFilter.value) {
    filtered = filtered.filter((f) => f.type === selectedTypeFilter.value)
  }

  return filtered
})

const formatDate = (date: string) => {
  return dayjs(date).format('MMM D, YYYY')
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const openFile = async (file: FileItem) => {
  if (file.type === 'model') {
    // Navigate to model page
    router.push(`/projects/${file.projectId}/models/${file.modelId}`)
    return
  }

  // For PDFs, open preview dialog
  if (file.type === 'pdf' && file.blobId) {
    previewFile.value = file
    previewError.value = null
    previewUrl.value = null
    showPreviewDialog.value = true

    try {
      previewUrl.value = await getBlobUrl({
        blobId: file.blobId,
        projectId: file.projectId
      })
    } catch (err) {
      previewError.value = err instanceof Error ? err.message : 'Failed to load PDF'
    }
  }
}

watch(showPreviewDialog, (isOpen) => {
  if (!isOpen) {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = null
    }
    previewFile.value = null
    previewError.value = null
  }
})
</script>
