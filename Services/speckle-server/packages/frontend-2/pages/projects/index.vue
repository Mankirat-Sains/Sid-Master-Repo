<template>
  <div>
    <Portal to="navigation">
      <HeaderNavLink :to="projectsRoute" name="Projects" :separator="false" />
    </Portal>

    <div class="max-w-4xl mx-auto py-8">
      <h1 class="text-heading-xl mb-8">Create New Project</h1>

      <!-- Project Creation Form -->
      <div class="bg-foundation-2 rounded-lg p-8 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-heading-lg">Project Details</h2>
          <FormButton color="outline" @click="showSelectFromDrive = true">
            Select Existing From Drive
          </FormButton>
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <FormTextInput
            name="projectName"
            label="Project Name"
            placeholder="Enter project name"
            color="foundation"
            :rules="[isRequired]"
            show-label
          />

          <FormTextInput
            name="projectNumber"
            label="Project Number"
            placeholder="Enter project number"
            color="foundation"
            show-label
            show-optional
          />

          <!-- File Upload Area -->
          <div>
            <FormFileUploadZone
              ref="uploadZone"
              v-slot="{ isDraggingFiles, openFilePicker }"
              :disabled="isCreating || isUploading"
              :accept="'.ifc,.rvt,.etabs,.xlsx,.pdf'"
              class="w-full"
              @files-selected="handleFilesSelected"
            >
              <div
                role="button"
                tabindex="0"
                class="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors"
                :class="[
                  isDraggingFiles
                    ? 'border-primary bg-primary-muted'
                    : 'border-outline-3',
                  isCreating || isUploading ? 'opacity-50 cursor-not-allowed' : ''
                ]"
                @click="openFilePicker"
                @keydown.enter="openFilePicker"
                @keydown.space.prevent="openFilePicker"
              >
                <IconUpload class="size-12 mx-auto mb-4 text-foreground-2" />
                <p class="text-heading-md mb-2">Upload File</p>
                <p class="text-sm text-foreground-2 mb-4">
                  Drag and drop files here or click to browse your local drive
                </p>
                <p class="text-xs text-foreground-3">
                  Supported formats: xlsx, ifc, rvt, etabs, PDF
                </p>

                <!-- Selected Files List -->
                <div v-if="selectedFiles.length" class="mt-6 text-left">
                  <p class="text-sm font-medium mb-2">Selected Files:</p>
                  <ul class="space-y-2">
                    <li v-for="file in selectedFiles" :key="file.name" class="text-sm">
                      <div class="flex items-center justify-between gap-2">
                        <span class="flex-1 truncate">{{ file.name }}</span>
                        <div class="flex items-center gap-2">
                          <button
                            v-if="canPreview(file) && !isUploading"
                            type="button"
                            class="text-primary hover:text-primary-focus text-xs"
                            @click.stop="openPreview(file)"
                          >
                            Preview
                          </button>
                          <button
                            v-if="!isUploading"
                            type="button"
                            class="text-danger hover:text-danger-focus text-xs"
                            @click.stop="removeFile(file)"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                      <!-- Upload Progress -->
                      <div
                        v-if="isUploading && uploadProgress[file.name] !== undefined"
                        class="mt-1"
                      >
                        <div class="flex items-center gap-2">
                          <div
                            class="flex-1 h-2 bg-foundation-3 rounded-full overflow-hidden"
                          >
                            <div
                              class="h-full bg-primary transition-all duration-300"
                              :style="{
                                width: `${uploadProgress[file.name]}%`
                              }"
                            ></div>
                          </div>
                          <span class="text-xs text-foreground-2">
                            {{ Math.round(uploadProgress[file.name]) }}%
                          </span>
                        </div>
                      </div>
                      <!-- Upload Error -->
                      <div
                        v-if="uploadErrors.find((e) => e.fileName === file.name)"
                        class="mt-1 text-xs text-danger"
                      >
                        {{ uploadErrors.find((e) => e.fileName === file.name)?.error }}
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </FormFileUploadZone>
          </div>

          <!-- Notes/Prompt Field -->
          <FormTextArea
            name="notes"
            label="Notes/Prompt"
            placeholder="Add any notes or instructions..."
            color="foundation"
            show-label
            show-optional
          />

          <!-- Action Buttons -->
          <div class="flex gap-3 justify-end pt-4">
            <FormButton
              type="button"
              color="outline"
              :disabled="isCreating || isUploading"
              @click="resetForm"
            >
              Cancel
            </FormButton>
            <FormButton
              type="submit"
              color="primary"
              :loading="isCreating || isUploading"
              :disabled="!canCreate"
            >
              {{ isUploading ? 'Uploading Files...' : 'Create Project' }}
            </FormButton>
          </div>
        </form>
      </div>
    </div>

    <!-- Create Project Dialog (for when workspace selection is needed) -->
    <ProjectsAdd v-model:open="showCreateDialog" @created="handleProjectCreated" />

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
          <template v-else-if="isPDFFile(previewFile.value) && previewUrl">
            <PdfViewer :url="previewUrl" />
          </template>
          <template v-else-if="isExcelFile(previewFile.value) && previewUrl">
            <ExcelViewer :url="previewUrl" />
          </template>
          <template v-else-if="isImageFile(previewFile.value) && previewUrl">
            <div class="flex justify-center overflow-auto bg-foundation-3 p-4 h-full">
              <img :src="previewUrl" alt="File preview" class="max-w-full max-h-full" />
            </div>
          </template>
          <template v-else>
            <div class="flex justify-center items-center h-full">
              <span class="text-body-sm text-foreground-2">
                Preview not available for this file type
              </span>
            </div>
          </template>
        </div>
      </template>
    </LayoutDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import { useCreateProject } from '~~/lib/projects/composables/projectManagement'
import { projectsRoute } from '~/lib/common/helpers/route'
import { useRouter } from 'vue-router'
import { isRequired } from '~~/lib/common/helpers/validation'
import { useMixpanel } from '~~/lib/core/composables/mp'
import { SupportedProjectVisibility } from '~/lib/projects/helpers/visibility'
import type { UploadableFileItem } from '@speckle/ui-components'
import PdfViewer from '~/components/file-viewers/PdfViewer.vue'
import ExcelViewer from '~/components/file-viewers/ExcelViewer.vue'
import { importFileLegacy } from '~~/lib/core/api/fileImport'
import { useAuthCookie } from '~~/lib/auth/composables/auth'
import { useApiOrigin } from '~/composables/env'
import { useGlobalToast, ToastNotificationType } from '~~/lib/common/composables/toast'

useHead({
  title: 'Create New Project'
})

definePageMeta({
  middleware: ['auth', 'projects-active-check']
})

const router = useRouter()
const uploadZone = ref()
const showCreateDialog = ref(false)
const showSelectFromDrive = ref(false)
const selectedFiles = ref<File[]>([])
const isCreating = ref(false)
const isUploading = ref(false)
const uploadProgress = ref<Record<string, number>>({})
const uploadErrors = ref<Array<{ fileName: string; error: string }>>([])
const showPreviewDialog = ref(false)
const previewFile = ref<File | null>(null)
const previewUrl = ref<string | null>(null)
const previewError = ref<string | null>(null)

const { handleSubmit, values } = useForm<{
  projectName: string
  projectNumber?: string
  notes?: string
}>()

const createProject = useCreateProject()
const mp = useMixpanel()
const logger = useLogger()
const authToken = useAuthCookie()
const apiOrigin = computed(() => useApiOrigin())
const { triggerNotification } = useGlobalToast()

// Handle file selection from FormFileUploadZone
const handleFilesSelected = (params: { files: UploadableFileItem[] }) => {
  // Convert UploadableFileItem[] to File[]
  selectedFiles.value = params.files.map((item) => item.file)
}

const canCreate = computed(() => {
  return values.projectName?.trim().length > 0 && !isUploading.value
})

const onSubmit = handleSubmit(async (formValues) => {
  if (isCreating.value || isUploading.value) return

  try {
    isCreating.value = true
    uploadErrors.value = []
    uploadProgress.value = {}

    // 1. Create the project
    logger.info(`[ProjectCreation] Creating project: ${formValues.projectName}`)
    const newProject = await createProject({
      name: formValues.projectName,
      description: formValues.notes || undefined,
      visibility: SupportedProjectVisibility.Private
    })

    if (!newProject?.id) {
      throw new Error('Failed to create project')
    }

    logger.info(`[ProjectCreation] Project created: ${newProject.id}`)

    // 2. Upload files if any
    if (selectedFiles.value.length > 0) {
      logger.info(
        `[ProjectCreation] Starting file uploads: ${selectedFiles.value.length} files`
      )
      isUploading.value = true
      isCreating.value = false // Allow UI to show upload progress

      const uploadPromises = selectedFiles.value.map(async (file) => {
        try {
          logger.info(
            `[FileUpload] Uploading ${file.name} to project ${newProject.id}...`
          )

          await importFileLegacy(
            {
              file,
              projectId: newProject.id,
              modelName: 'main', // API will create model if needed
              modelId: '', // Not needed for autodetect endpoint
              apiOrigin: apiOrigin.value,
              authToken: authToken.value || ''
            },
            {
              onProgress: (percentage) => {
                uploadProgress.value[file.name] = percentage
              }
            }
          )

          logger.info(
            `[FileUpload] Success: ${file.name} uploaded, fileimport-service will process it`
          )
          uploadProgress.value[file.name] = 100
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : 'Unknown error'
          logger.error(`[FileUpload] Error: ${file.name} - ${errorMsg}`)
          uploadErrors.value.push({ fileName: file.name, error: errorMsg })
          uploadProgress.value[file.name] = 0
        }
      })

      // Wait for all uploads to complete
      await Promise.allSettled(uploadPromises)

      isUploading.value = false

      // Show notifications for results
      if (uploadErrors.value.length > 0) {
        logger.warn(
          `[ProjectCreation] Some uploads failed: ${uploadErrors.value.length} errors`
        )
        triggerNotification({
          type: ToastNotificationType.Warning,
          title: 'Some files failed to upload',
          description: `${uploadErrors.value.length} file(s) failed. Check console for details.`
        })
      } else {
        logger.info(`[ProjectCreation] All uploads completed successfully`)
        triggerNotification({
          type: ToastNotificationType.Success,
          title: 'Files uploaded successfully',
          description: `${selectedFiles.value.length} file(s) are being processed.`
        })
      }
    }

    // 3. Navigate to the new project
    router.push(`/projects/${newProject.id}`)

    // 4. Track analytics
    mp.track('Stream Action', {
      type: 'action',
      name: 'create',
      location: 'landing_page'
    })
  } catch (error) {
    logger.error('[ProjectCreation] Failed to create project:', error)
    triggerNotification({
      type: ToastNotificationType.Danger,
      title: 'Failed to create project',
      description: error instanceof Error ? error.message : 'An unknown error occurred'
    })
  } finally {
    isCreating.value = false
    isUploading.value = false
  }
})

const handleProjectCreated = (project: { id: string }) => {
  // Handle project created from dialog
  router.push(`/projects/${project.id}`)
}

const removeFile = (file: File) => {
  selectedFiles.value = selectedFiles.value.filter((f) => f !== file)
}

const resetForm = () => {
  selectedFiles.value = []
  uploadProgress.value = {}
  uploadErrors.value = []
  isUploading.value = false
  // Reset form
  handleSubmit(() => {})()
}

const getFileExtension = (fileName: string): string => {
  const parts = fileName.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
}

const isPDFFile = (file: File): boolean => {
  return getFileExtension(file.name) === 'pdf'
}

const isExcelFile = (file: File): boolean => {
  const ext = getFileExtension(file.name)
  return ['xlsx', 'xls'].includes(ext)
}

const isImageFile = (file: File): boolean => {
  const ext = getFileExtension(file.name)
  return ['jpg', 'jpeg', 'png', 'gif'].includes(ext)
}

const canPreview = (file: File): boolean => {
  return isPDFFile(file) || isExcelFile(file) || isImageFile(file)
}

const openPreview = async (file: File) => {
  previewFile.value = file
  previewError.value = null
  previewUrl.value = null
  showPreviewDialog.value = true

  try {
    // Create object URL for local file preview
    previewUrl.value = URL.createObjectURL(file)
  } catch (err) {
    previewError.value =
      err instanceof Error ? err.message : 'Failed to load file preview'
  }
}

watch(showPreviewDialog, (isOpen) => {
  if (!isOpen) {
    // Clean up object URL when dialog closes
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = null
    }
    previewFile.value = null
    previewError.value = null
  }
})
</script>
