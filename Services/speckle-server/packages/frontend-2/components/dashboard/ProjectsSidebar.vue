<template>
  <LayoutSidebar class="w-full">
    <div class="flex flex-col divide-y divide-outline-3">
      <!-- Projects Section -->
      <div class="px-2 pt-3 pb-2">
        <h2 class="text-sm font-semibold text-foreground mb-3">Projects</h2>
        <div class="flex flex-col gap-1">
          <div v-for="project in projects" :key="project.id" class="flex flex-col">
            <!-- Project Header (Clickable to expand/collapse) -->
            <div class="relative">
              <button
                class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left"
                :class="isProjectActive(project.id) ? 'bg-foundation-2' : ''"
                @click="toggleProject(project.id)"
                @contextmenu.prevent="openContextMenu($event, project)"
              >
                <ChevronDown
                  v-if="expandedProjects.has(project.id)"
                  class="size-4 text-foreground-2 flex-shrink-0"
                />
                <ChevronRight v-else class="size-4 text-foreground-2 flex-shrink-0" />
                <IconProjects class="size-4 text-foreground-2 flex-shrink-0" />
                <span class="text-sm text-foreground flex-1 truncate">
                  {{ project.name || project.id }}
                </span>
              </button>

              <!-- Context Menu -->
              <div
                v-if="contextMenuOpen[project.id]"
                class="fixed z-50 bg-foundation shadow-lg border border-outline-2 rounded-md overflow-hidden"
                :style="{
                  left: `${contextMenuPosition.x}px`,
                  top: `${contextMenuPosition.y}px`
                }"
              >
                <button
                  v-for="item in contextMenuItems[0]"
                  :key="item.id"
                  class="w-full px-4 py-2 text-left text-sm text-danger hover:bg-danger hover:text-foreground-on-primary flex items-center gap-2"
                  @click.stop="onContextMenuChosen(item, project)"
                >
                  <component :is="item.icon" class="size-4" />
                  <span>{{ item.title }}</span>
                </button>
              </div>
            </div>

            <!-- Nested Folders (Models and PDFs) -->
            <div
              v-if="expandedProjects.has(project.id)"
              class="ml-6 mt-1 flex flex-col gap-1"
            >
              <!-- Models Folder -->
              <div class="flex flex-col">
                <button
                  class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left"
                  @click="toggleFolder(project.id, 'models')"
                >
                  <ChevronDown
                    v-if="expandedFolders.has(`${project.id}-models`)"
                    class="size-4 text-foreground-2 flex-shrink-0"
                  />
                  <ChevronRight v-else class="size-4 text-foreground-2 flex-shrink-0" />
                  <Folder class="size-4 text-foreground-2 flex-shrink-0" />
                  <span class="text-sm text-foreground-2">Models</span>
                </button>

                <!-- Models List -->
                <div
                  v-if="expandedFolders.has(`${project.id}-models`)"
                  class="ml-6 mt-1 flex flex-col gap-1"
                >
                  <div
                    v-if="projectModels[project.id]?.loading"
                    class="px-2 py-1.5 text-sm text-foreground-3"
                  >
                    Loading...
                  </div>
                  <div
                    v-else-if="
                      !projectModels[project.id]?.models?.length &&
                      projectModels[project.id]?.models !== undefined
                    "
                    class="px-2 py-1.5 text-sm text-foreground-3"
                  >
                    No models
                  </div>
                  <button
                    v-for="model in projectModels[project.id]?.models || []"
                    :key="model.id"
                    class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left"
                    :class="
                      isModelActive(project.id, model.id) ? 'bg-foundation-2' : ''
                    "
                    @click="openModel(project.id, model.id)"
                  >
                    <Box class="size-4 text-foreground-2 flex-shrink-0" />
                    <span class="text-sm text-foreground flex-1 truncate">
                      {{ model.name }}
                    </span>
                  </button>
                  <!-- Add Model Button -->
                  <button
                    class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left text-sm text-foreground-2"
                    @click.stop="addModel(project.id)"
                  >
                    <Plus class="size-4 text-foreground-2 flex-shrink-0" />
                    <span>Add model</span>
                  </button>
                </div>
              </div>

              <!-- PDFs Folder -->
              <div class="flex flex-col">
                <button
                  class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left"
                  @click="toggleFolder(project.id, 'pdfs')"
                >
                  <ChevronDown
                    v-if="expandedFolders.has(`${project.id}-pdfs`)"
                    class="size-4 text-foreground-2 flex-shrink-0"
                  />
                  <ChevronRight v-else class="size-4 text-foreground-2 flex-shrink-0" />
                  <Folder class="size-4 text-foreground-2 flex-shrink-0" />
                  <span class="text-sm text-foreground-2">PDFs</span>
                </button>

                <!-- PDFs List -->
                <div
                  v-if="expandedFolders.has(`${project.id}-pdfs`)"
                  class="ml-6 mt-1 flex flex-col gap-1"
                >
                  <div
                    v-if="projectPdfs[project.id]?.loading"
                    class="px-2 py-1.5 text-sm text-foreground-3"
                  >
                    Loading...
                  </div>
                  <div
                    v-else-if="
                      !projectPdfs[project.id]?.pdfs?.length &&
                      projectPdfs[project.id]?.pdfs !== undefined
                    "
                    class="px-2 py-1.5 text-sm text-foreground-3"
                  >
                    No PDFs
                  </div>
                  <button
                    v-for="pdf in projectPdfs[project.id]?.pdfs || []"
                    :key="pdf.id"
                    class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left"
                    :class="isPdfActive(project.id, pdf.id) ? 'bg-foundation-2' : ''"
                    @click="openPdf(project.id, pdf)"
                  >
                    <FileText class="size-4 text-foreground-2 flex-shrink-0" />
                    <span class="text-sm text-foreground flex-1 truncate">
                      {{ pdf.name }}
                    </span>
                  </button>
                  <!-- Add PDF Button -->
                  <button
                    class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2 w-full text-left text-sm text-foreground-2"
                    @click.stop="addPdf(project.id)"
                  >
                    <Plus class="size-4 text-foreground-2 flex-shrink-0" />
                    <span>Add PDF</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Files Section -->
      <div class="px-2 pt-3 pb-2">
        <h2 class="text-sm font-semibold text-foreground mb-3">Files</h2>
        <NuxtLink
          to="/files"
          class="px-2 py-1.5 rounded-md hover:bg-foundation-2 transition-colors flex items-center gap-2"
          :class="route.path === '/files' ? 'bg-foundation-2' : ''"
        >
          <Folder class="size-4 text-foreground-2" />
          <span class="text-sm text-foreground">All Files</span>
        </NuxtLink>
      </div>

      <!-- Other Navigation -->
      <LayoutSidebarMenu>
        <LayoutSidebarMenuGroup title="Resources" collapsible>
          <NuxtLink :to="connectorsRoute">
            <LayoutSidebarMenuGroupItem
              label="Connectors"
              :active="isActive(connectorsRoute)"
            >
              <template #icon>
                <IconConnectors class="size-4 text-foreground-2" />
              </template>
            </LayoutSidebarMenuGroupItem>
          </NuxtLink>

          <NuxtLink :to="tutorialsRoute">
            <LayoutSidebarMenuGroupItem
              label="Documentation"
              :active="isActive(tutorialsRoute)"
            >
              <template #icon>
                <IconDocumentation class="size-4 text-foreground-2" />
              </template>
            </LayoutSidebarMenuGroupItem>
          </NuxtLink>
        </LayoutSidebarMenuGroup>
      </LayoutSidebarMenu>
    </div>
  </LayoutSidebar>

  <!-- PDF Preview Dialog -->
  <LayoutDialog
    v-model:open="showPdfDialog"
    max-width="lg"
    :buttons="[{ text: 'Close', onClick: () => (showPdfDialog = false) }]"
  >
    <template #header>
      {{ selectedPdf?.name || 'PDF Preview' }}
    </template>
    <template v-if="selectedPdf && pdfPreviewUrl">
      <div class="flex flex-col space-y-2 h-[600px]">
        <PdfViewer :url="pdfPreviewUrl" />
      </div>
    </template>
    <template v-else-if="pdfLoading">
      <div class="flex justify-center items-center h-[600px]">
        <Loader2 class="size-8 animate-spin text-foreground-2" />
      </div>
    </template>
    <template v-else-if="pdfError">
      <div class="flex justify-center items-center h-[600px]">
        <span class="inline-flex space-x-2 items-center text-danger">
          {{ pdfError }}
        </span>
      </div>
    </template>
  </LayoutDialog>

  <!-- Delete Project Dialog -->
  <ClientOnly>
    <ProjectsDeleteDialog
      v-if="selectedProjectForDelete"
      v-model:open="showDeleteDialog"
      :project="selectedProjectForDelete"
      :redirect-on-complete="false"
    />
  </ClientOnly>
</template>

<script setup lang="ts">
import { useQuery, useLazyQuery, useApolloClient } from '@vue/apollo-composable'
import {
  projectsWithModelsQuery,
  projectPdfsQuery
} from '~~/lib/projects/graphql/queries'
import { useRoute, useRouter } from 'vue-router'
import {
  connectorsRoute,
  tutorialsRoute,
  projectRoute
} from '~/lib/common/helpers/route'
import {
  Folder,
  ChevronDown,
  ChevronRight,
  Box,
  FileText,
  Loader2,
  Plus,
  Trash2
} from 'lucide-vue-next'
import { useFileDownload } from '~~/lib/core/composables/fileUpload'
import PdfViewer from '~/components/file-viewers/PdfViewer.vue'
import ProjectsDeleteDialog from '~/components/projects/DeleteDialog.vue'
import type { LayoutMenuItem } from '~~/lib/layout/helpers/components'
import { graphql } from '~~/lib/common/generated/gql'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const route = useRoute()
const router = useRouter()
const { getBlobUrl } = useFileDownload()
const apolloClient = useApolloClient().client

// Expanded state tracking
const expandedProjects = ref<Set<string>>(new Set())
const expandedFolders = ref<Set<string>>(new Set())

// Project models and PDFs data
const projectModels = ref<Record<string, { models: any[]; loading: boolean }>>({})
const projectPdfs = ref<Record<string, { pdfs: any[]; loading: boolean }>>({})

// PDF preview state
const showPdfDialog = ref(false)
const selectedPdf = ref<{
  id: string
  name: string
  projectId: string
  blobId?: string
} | null>(null)
const pdfPreviewUrl = ref<string | null>(null)
const pdfLoading = ref(false)
const pdfError = ref<string | null>(null)

// Context menu state
const contextMenuOpen = ref<Record<string, boolean>>({})
const contextMenuPosition = ref<{ x: number; y: number }>({ x: 0, y: 0 })

// Delete dialog state
const showDeleteDialog = ref(false)
const selectedProjectForDelete = ref<any>(null)

// GraphQL query for project details needed for deletion
const projectDeleteQuery = graphql(`
  query ProjectDeleteInfo($id: String!) {
    project(id: $id) {
      id
      name
      role
      models(limit: 0) {
        totalCount
      }
      workspace {
        slug
        id
      }
      versions(limit: 0) {
        totalCount
      }
      permissions {
        canDelete {
          authorized
          code
          message
        }
      }
    }
  }
`)

const {
  result: projectDeleteResult,
  loading: loadingProjectDelete,
  load: loadProjectDelete
} = useLazyQuery(projectDeleteQuery, () => ({
  id: selectedProjectForDelete.value?.id || ''
}))

const contextMenuItems = computed<LayoutMenuItem[][]>(() => [
  [
    {
      title: 'Delete',
      id: 'delete',
      icon: Trash2,
      props: {
        color: 'danger'
      }
    }
  ]
])

const { result: projectsResult } = useQuery(projectsWithModelsQuery, () => ({
  filter: {
    personalOnly: false
  },
  cursor: null
}))

const projects = computed(() => {
  return projectsResult.value?.activeUser?.projects?.items || []
})

// Watch route changes to refetch PDFs when navigating to a project
watch(
  () => route.params.id,
  (newProjectId) => {
    if (newProjectId && typeof newProjectId === 'string') {
      const folderKey = `${newProjectId}-pdfs`
      // If PDFs folder is expanded, force a refetch
      if (expandedFolders.value.has(folderKey)) {
        console.log(
          '[ProjectsSidebar] Project changed, refetching PDFs for:',
          newProjectId
        )
        fetchProjectPdfs(newProjectId, true)
      }
    }
  }
)

// Initialize project models when projects are loaded
watch(
  projects,
  (newProjects) => {
    for (const project of newProjects) {
      if (!projectModels.value[project.id]) {
        projectModels.value[project.id] = {
          models: project.models?.items || [],
          loading: false
        }
      }
      // Initialize PDFs as empty for now (can be populated later)
      if (!projectPdfs.value[project.id]) {
        projectPdfs.value[project.id] = {
          pdfs: [],
          loading: false
        }
      }
    }
  },
  { immediate: true }
)

// Auto-expand current project and folder when route changes
watch(
  () => route.params,
  (params) => {
    if (params.id) {
      const projectId = params.id as string
      // Expand project if viewing a project page
      if (!expandedProjects.value.has(projectId)) {
        expandedProjects.value.add(projectId)
      }
      // Expand models folder if viewing a model
      if (params.modelId && route.path.includes('/models/')) {
        expandedFolders.value.add(`${projectId}-models`)
      }
    }
  },
  { immediate: true }
)

const toggleProject = (projectId: string) => {
  if (expandedProjects.value.has(projectId)) {
    expandedProjects.value.delete(projectId)
    // Also collapse folders when collapsing project
    expandedFolders.value.delete(`${projectId}-models`)
    expandedFolders.value.delete(`${projectId}-pdfs`)
  } else {
    expandedProjects.value.add(projectId)
  }
}

// Fetch PDFs for a project when PDFs folder is expanded
const fetchProjectPdfs = async (projectId: string, forceRefetch = false) => {
  // Initialize if not exists
  if (!projectPdfs.value[projectId]) {
    projectPdfs.value[projectId] = {
      pdfs: [],
      loading: true
    }
  }

  // Don't fetch if already loading (unless forcing refetch)
  if (!forceRefetch && projectPdfs.value[projectId].loading) {
    return
  }

  // If we already have PDFs and not forcing refetch, don't fetch again
  if (!forceRefetch && projectPdfs.value[projectId].pdfs.length > 0) {
    return
  }

  // Set loading state
  projectPdfs.value[projectId].loading = true

  try {
    console.log('[ProjectsSidebar] Fetching PDFs for project:', projectId)

    // Check if query exists
    if (!projectPdfsQuery) {
      console.error('[ProjectsSidebar] projectPdfsQuery is undefined!')
      throw new Error('PDF query not available')
    }

    // @ts-ignore - projectPdfsQuery needs codegen
    const result = await (apolloClient.query as any)({
      query: projectPdfsQuery,
      variables: {
        projectId,
        limit: 100,
        cursor: null,
        query: null
      },
      // @ts-ignore - fetchPolicy type
      fetchPolicy: forceRefetch ? 'network-only' : 'cache-and-network',
      errorPolicy: 'all' // Handle errors gracefully
    })

    console.log('[ProjectsSidebar] PDF query result:', result.data)

    if (result.errors) {
      console.error('[ProjectsSidebar] GraphQL errors:', result.errors)
    }

    if (result.data?.project?.blobs?.items) {
      // Filter for PDFs: check fileType or fileName
      const allBlobs = result.data.project.blobs.items
      console.log('[ProjectsSidebar] All blobs:', allBlobs.length)

      const pdfs = allBlobs
        .filter((blob: any) => {
          const fileType = blob.fileType?.toLowerCase()
          const fileName = blob.fileName?.toLowerCase() || ''

          // Check fileType: 'pdf', 'application/pdf', or fileName ends with .pdf
          return (
            fileType === 'pdf' ||
            fileType === 'application/pdf' ||
            fileName.endsWith('.pdf')
          )
        })
        .map((blob: any) => ({
          id: blob.id,
          name: blob.fileName || blob.id,
          blobId: blob.id,
          createdAt: blob.createdAt,
          fileSize: blob.fileSize
        }))

      console.log('[ProjectsSidebar] Filtered PDFs:', pdfs.length, pdfs)

      projectPdfs.value[projectId] = {
        pdfs,
        loading: false
      }
    } else {
      console.log('[ProjectsSidebar] No blobs found in result')
      projectPdfs.value[projectId] = {
        pdfs: [],
        loading: false
      }
    }
  } catch (error: any) {
    console.error('[ProjectsSidebar] Failed to fetch PDFs:', error)
    console.error('[ProjectsSidebar] Error details:', {
      message: error?.message,
      graphQLErrors: error?.graphQLErrors,
      networkError: error?.networkError,
      stack: error?.stack
    })
    projectPdfs.value[projectId] = {
      pdfs: [],
      loading: false
    }
  }
}

const toggleFolder = (projectId: string, folderType: 'models' | 'pdfs') => {
  const folderKey = `${projectId}-${folderType}`
  if (expandedFolders.value.has(folderKey)) {
    expandedFolders.value.delete(folderKey)
  } else {
    expandedFolders.value.add(folderKey)
    // Fetch PDFs when PDFs folder is expanded
    if (folderType === 'pdfs') {
      fetchProjectPdfs(projectId)
    }
  }
}

const isProjectActive = (projectId: string): boolean => {
  return route.params.id === projectId
}

const isModelActive = (projectId: string, modelId: string): boolean => {
  return (
    route.params.id === projectId &&
    route.params.modelId === modelId &&
    route.path.includes('/models/')
  )
}

const isPdfActive = (projectId: string, pdfId: string): boolean => {
  return false // PDFs don't have routes yet
}

const openModel = (projectId: string, modelId: string) => {
  router.push(`/projects/${projectId}/models/${modelId}`)
}

const openPdf = async (
  projectId: string,
  pdf: { id: string; name: string; blobId?: string }
) => {
  selectedPdf.value = { ...pdf, projectId }
  showPdfDialog.value = true
  pdfLoading.value = true
  pdfError.value = null
  pdfPreviewUrl.value = null

  // Use blobId if available, otherwise use id (blob ID is same as PDF ID)
  const blobIdToUse = pdf.blobId || pdf.id
  if (blobIdToUse) {
    try {
      pdfPreviewUrl.value = await getBlobUrl({
        blobId: blobIdToUse,
        projectId
      })
    } catch (err) {
      pdfError.value = err instanceof Error ? err.message : 'Failed to load PDF'
    } finally {
      pdfLoading.value = false
    }
  } else {
    pdfError.value = 'PDF blob ID not available'
    pdfLoading.value = false
  }
}

watch(showPdfDialog, (isOpen) => {
  if (!isOpen) {
    if (pdfPreviewUrl.value) {
      URL.revokeObjectURL(pdfPreviewUrl.value)
      pdfPreviewUrl.value = null
    }
    selectedPdf.value = null
    pdfError.value = null
    pdfLoading.value = false
  }
})

watch(showDeleteDialog, (isOpen) => {
  if (!isOpen) {
    selectedProjectForDelete.value = null
  }
})

const isActive = (routePath: string | { id: string }): boolean => {
  if (typeof routePath === 'object') {
    return route.params.id === routePath.id
  }
  return route.path === routePath
}

const openContextMenu = (event: MouseEvent, project: any) => {
  event.preventDefault()
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuOpen.value = { [project.id]: true }
}

const onContextMenuChosen = (item: LayoutMenuItem, project: any) => {
  if (item.id === 'delete') {
    // Ensure we have a valid project before opening the dialog
    if (project && project.id) {
      selectedProjectForDelete.value = project
      // Fetch full project details for the delete dialog
      loadProjectDelete()
    }
  }
  contextMenuOpen.value = { [project.id]: false }
}

// Watch for project delete result and open dialog when ready
watch(projectDeleteResult, (newResult) => {
  if (
    newResult?.project &&
    selectedProjectForDelete.value?.id === newResult.project.id
  ) {
    selectedProjectForDelete.value = newResult.project
    showDeleteDialog.value = true
  }
})

const addPdf = async (projectId: string) => {
  const targetRoute = `/projects/${projectId}/add/pdf`
  console.log('[ProjectsSidebar] Navigating to PDF upload page:', targetRoute)
  console.log('[ProjectsSidebar] Current route:', route.path)
  console.log(
    '[ProjectsSidebar] Router available routes:',
    router.getRoutes().filter((r) => r.path.includes('/add'))
  )

  // Use router.push with explicit path to ensure it works
  try {
    await router.push(targetRoute)
    console.log('[ProjectsSidebar] Navigation successful, new route:', route.path)
  } catch (error: any) {
    console.error('[ProjectsSidebar] Navigation failed:', error)
    // If route doesn't exist, try alternative approach
    if (error?.code === 404 || error?.message?.includes('not found')) {
      console.warn('[ProjectsSidebar] Route not found, trying alternative navigation')
      // Fallback: navigate to project page
      await router.push(projectRoute(projectId))
    } else {
      throw error
    }
  }
}

const addModel = async (projectId: string) => {
  const targetRoute = `/projects/${projectId}/add/model`
  console.log('[ProjectsSidebar] Navigating to Model upload page:', targetRoute)
  console.log('[ProjectsSidebar] Current route:', route.path)

  try {
    await router.push(targetRoute)
    console.log('[ProjectsSidebar] Navigation successful, new route:', route.path)
  } catch (error: any) {
    console.error('[ProjectsSidebar] Navigation failed:', error)
    // If route doesn't exist, try alternative approach
    if (error?.code === 404 || error?.message?.includes('not found')) {
      console.warn('[ProjectsSidebar] Route not found, trying alternative navigation')
      // Fallback: navigate to project page
      await router.push(projectRoute(projectId))
    } else {
      throw error
    }
  }
}

// Close context menu when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const isContextMenuOpen = Object.values(contextMenuOpen.value).some((val) => val)
  if (isContextMenuOpen) {
    contextMenuOpen.value = {}
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
