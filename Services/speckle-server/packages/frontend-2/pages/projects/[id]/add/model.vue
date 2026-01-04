<template>
  <div>
    <Portal to="navigation">
      <HeaderNavLink :to="projectsRoute" name="Projects" :separator="false" />
      <HeaderNavLink
        :to="projectRoute(projectId)"
        :name="project?.name || 'Project'"
        :separator="false"
      />
      <HeaderNavLink name="Add Model" :separator="false" />
    </Portal>

    <div class="max-w-4xl mx-auto py-8">
      <h1 class="text-heading-xl mb-8">Add Model to Project</h1>

      <!-- File Upload Area -->
      <div class="bg-foundation-2 rounded-lg p-8">
        <FormFileUploadZone
          ref="uploadZone"
          v-slot="{ isDraggingFiles, openFilePicker }"
          :disabled="isUploading"
          :accept="'.ifc,.rvt,.etabs,.xlsx,.obj,.fbx,.dae'"
          class="w-full"
          @files-selected="handleFilesSelected"
        >
          <div
            role="button"
            tabindex="0"
            class="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors"
            :class="[
              isDraggingFiles ? 'border-primary bg-primary-muted' : 'border-outline-3',
              isUploading ? 'opacity-50 cursor-not-allowed' : ''
            ]"
            @click="openFilePicker"
            @keydown.enter="openFilePicker"
            @keydown.space.prevent="openFilePicker"
          >
            <IconUpload class="size-12 mx-auto mb-4 text-foreground-2" />
            <p class="text-heading-md mb-2">Upload Model File</p>
            <p class="text-sm text-foreground-2 mb-4">
              Drag and drop model files here or click to browse your local drive
            </p>
            <p class="text-xs text-foreground-3">
              Supported formats: IFC, RVT, ETABS, OBJ, FBX, DAE, XLSX
            </p>

            <!-- Selected Files List -->
            <div v-if="selectedFiles.length" class="mt-6 text-left">
              <p class="text-sm font-medium mb-2">Selected Files:</p>
              <ul class="space-y-2">
                <li v-for="file in selectedFiles" :key="file.name" class="text-sm">
                  <div class="flex items-center justify-between gap-2">
                    <span class="flex-1 truncate">{{ file.name }}</span>
                    <button
                      v-if="!isUploading"
                      type="button"
                      class="text-danger hover:text-danger-focus text-xs"
                      @click.stop="removeFile(file)"
                    >
                      Remove
                    </button>
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

        <!-- Action Buttons -->
        <div class="flex gap-3 justify-end mt-6">
          <FormButton
            type="button"
            color="outline"
            :disabled="isUploading"
            @click="cancel"
          >
            Cancel
          </FormButton>
          <FormButton
            type="button"
            color="primary"
            :disabled="selectedFiles.length === 0 || isUploading"
            @click="uploadFiles"
          >
            {{ isUploading ? 'Uploading...' : 'Upload Model' }}
          </FormButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFileUpload } from '~~/lib/core/composables/fileUpload'
import { projectsRoute, projectRoute } from '~/lib/common/helpers/route'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'
import type { UploadableFileItem } from '@speckle/ui-components'

definePageMeta({
  middleware: ['auth', 'require-valid-project'],
  layout: 'default'
})

useHead({
  title: 'Add Model'
})

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.id as string)

const { uploadFiles: uploadFilesToProject } = useFileUpload()
const uploadZone = ref()
const selectedFiles = ref<UploadableFileItem[]>([])
const isUploading = ref(false)
const uploadProgress = ref<Record<string, number>>({})
const uploadErrors = ref<Array<{ fileName: string; error: string }>>([])

const handleFilesSelected = (params: { files: UploadableFileItem[] }) => {
  selectedFiles.value = [...selectedFiles.value, ...params.files]
  uploadErrors.value = uploadErrors.value.filter(
    (e) => !params.files.some((f) => f.name === e.fileName)
  )
}

const removeFile = (file: UploadableFileItem) => {
  selectedFiles.value = selectedFiles.value.filter((f) => f !== file)
  uploadErrors.value = uploadErrors.value.filter((e) => e.fileName !== file.name)
  delete uploadProgress.value[file.name]
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return

  isUploading.value = true
  uploadErrors.value = []

  try {
    const uploadResults = uploadFilesToProject(
      selectedFiles.value,
      { streamId: projectId.value },
      (uploadedFiles) => {
        // Update progress for each file
        for (const [fileId, uploadFile] of Object.entries(uploadedFiles)) {
          const file = selectedFiles.value.find((f) => f.id === fileId)
          if (file) {
            uploadProgress.value[file.name] = uploadFile.progress || 0

            // Check for errors
            if (uploadFile.error) {
              uploadErrors.value.push({
                fileName: file.name,
                error: uploadFile.error
              })
            } else if (uploadFile.result?.uploadError) {
              uploadErrors.value.push({
                fileName: file.name,
                error: uploadFile.result.uploadError
              })
            }
          }
        }
      }
    )

    // Wait for uploads to complete
    await new Promise<void>((resolve) => {
      const checkComplete = setInterval(() => {
        const allComplete = selectedFiles.value.every((file) => {
          const uploadFile = uploadResults[file.id]
          return uploadFile && (uploadFile.progress === 100 || uploadFile.error)
        })

        if (allComplete) {
          clearInterval(checkComplete)
          resolve()
        }
      }, 100)
    })

    // Check final results
    for (const file of selectedFiles.value) {
      const uploadFile = uploadResults[file.id]
      if (uploadFile?.error) {
        uploadErrors.value.push({
          fileName: file.name,
          error: uploadFile.error
        })
      } else if (uploadFile?.result?.uploadError) {
        uploadErrors.value.push({
          fileName: file.name,
          error: uploadFile.result.uploadError
        })
      } else if (uploadFile?.result?.blobId) {
        uploadProgress.value[file.name] = 100
      }
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Upload failed'
    uploadErrors.value.push({ fileName: 'Upload', error: errorMsg })
    console.error('Failed to upload files:', error)
  }

  isUploading.value = false

  // If all files uploaded successfully, navigate back
  if (uploadErrors.value.length === 0) {
    router.push(projectRoute(projectId.value))
  }
}

const cancel = () => {
  router.push(projectRoute(projectId.value))
}

// Fetch project info (optional, for display)
const project = computed(() => null)
</script>
