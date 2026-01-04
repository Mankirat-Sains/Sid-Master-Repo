<template>
  <div>
    <Portal to="navigation">
      <HeaderNavLink :to="projectsRoute" name="Projects" :separator="false" />
      <HeaderNavLink
        :to="projectRoute(projectId)"
        :name="'Project'"
        :separator="false"
      />
      <HeaderNavLink name="Add PDF" :separator="false" />
    </Portal>

    <div class="max-w-4xl mx-auto py-8">
      <h1 class="text-heading-xl mb-8">Add PDF to Project</h1>

      <!-- File Upload Area -->
      <div class="bg-foundation-2 rounded-lg p-8">
        <FormFileUploadZone
          ref="uploadZone"
          v-slot="{ isDraggingFiles, openFilePicker }"
          :disabled="isUploading"
          :accept="'.pdf'"
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
            <p class="text-heading-md mb-2">Upload PDF File</p>
            <p class="text-sm text-foreground-2 mb-4">
              Drag and drop PDF files here or click to browse your local drive
            </p>
            <p class="text-xs text-foreground-3">Supported format: PDF</p>

            <!-- Selected Files List -->
            <div v-if="selectedFiles.length" class="mt-6 text-left">
              <p class="text-sm font-medium mb-2">Selected Files:</p>
              <ul class="space-y-2">
                <li v-for="file in selectedFiles" :key="file.id" class="text-sm">
                  <div class="flex items-center justify-between gap-2">
                    <span class="flex-1 truncate">{{ file.file.name }}</span>
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
                    v-if="isUploading && uploadProgress[file.id] !== undefined"
                    class="mt-1"
                  >
                    <div class="flex items-center gap-2">
                      <div
                        class="flex-1 h-2 bg-foundation-3 rounded-full overflow-hidden"
                      >
                        <div
                          class="h-full bg-primary transition-all duration-300"
                          :style="{
                            width: `${uploadProgress[file.id]}%`
                          }"
                        ></div>
                      </div>
                      <span class="text-xs text-foreground-2">
                        {{ Math.round(uploadProgress[file.id]) }}%
                      </span>
                    </div>
                  </div>
                  <!-- Upload Error -->
                  <div
                    v-if="uploadErrors.find((e) => e.fileName === file.id)"
                    class="mt-1 text-xs text-danger"
                  >
                    {{ uploadErrors.find((e) => e.fileName === file.id)?.error }}
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
            {{ isUploading ? 'Uploading...' : 'Upload PDF' }}
          </FormButton>
        </div>

        <!-- Success Message -->
        <div
          v-if="!isUploading && uploadErrors.length === 0 && uploadSuccessCount > 0"
          class="mt-4 p-4 bg-success/10 border border-success/20 rounded-lg"
        >
          <p class="text-sm text-success font-medium">
            Successfully uploaded {{ uploadSuccessCount }} PDF(s)!
          </p>
          <div class="flex gap-3 mt-3">
            <FormButton type="button" color="primary" size="sm" @click="goToProject">
              View Project
            </FormButton>
            <FormButton type="button" color="outline" size="sm" @click="resetUpload">
              Upload Another
            </FormButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFileUpload } from '~~/lib/core/composables/fileUpload'
import { projectsRoute, projectRoute } from '~/lib/common/helpers/route'
import { useRoute, useRouter } from 'vue-router'
import { useApolloClient } from '@vue/apollo-composable'
import { ref, computed, onMounted } from 'vue'
import type { UploadableFileItem, UploadFileItem } from '@speckle/ui-components'

// Debug logging
console.log('🟢 [AddPDF] Script setup executing!')
console.log('🟢 [AddPDF] File loaded at:', new Date().toISOString())

definePageMeta({
  middleware: ['auth', 'require-valid-project'],
  layout: 'default'
})

useHead({
  title: 'Add PDF'
})

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.id as string)
const apolloClient = useApolloClient().client

// Debug logging on mount
onMounted(() => {
  console.log('🟢 [AddPDF] Component MOUNTED!')
  console.log('🟢 [AddPDF] Route path:', route.path)
  console.log('🟢 [AddPDF] Route params:', route.params)
  console.log('🟢 [AddPDF] Project ID:', projectId.value)
  console.log('🟢 [AddPDF] Apollo client exists:', !!apolloClient)
})

const { uploadFiles: uploadFilesToProject } = useFileUpload()
const uploadZone = ref()
const selectedFiles = ref<UploadableFileItem[]>([])
const isUploading = ref(false)
const uploadProgress = ref<Record<string, number>>({})
const uploadErrors = ref<Array<{ fileName: string; error: string }>>([])
const uploadSuccessCount = ref(0)

const handleFilesSelected = (params: { files: UploadableFileItem[] }) => {
  selectedFiles.value = [...selectedFiles.value, ...params.files]
  uploadErrors.value = uploadErrors.value.filter(
    (e) => !params.files.some((f) => f.id === e.fileName)
  )
}

const removeFile = (file: UploadableFileItem) => {
  selectedFiles.value = selectedFiles.value.filter((f) => f !== file)
  uploadErrors.value = uploadErrors.value.filter((e) => e.fileName !== file.id)
  delete uploadProgress.value[file.id]
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return

  console.log('📤 [AddPDF] Starting upload...', {
    fileCount: selectedFiles.value.length,
    projectId: projectId.value,
    files: selectedFiles.value.map((f) => f.file.name)
  })

  isUploading.value = true
  uploadErrors.value = []
  uploadSuccessCount.value = 0

  let uploadResults: Record<string, UploadFileItem> = {}
  try {
    uploadResults = uploadFilesToProject(
      selectedFiles.value,
      { streamId: projectId.value },
      (uploadedFiles) => {
        console.log('📊 [AddPDF] Upload progress update:', uploadedFiles)
        // Update progress for each file
        for (const [fileId, uploadFile] of Object.entries(uploadedFiles)) {
          const file = selectedFiles.value.find((f) => f.id === fileId)
          if (file) {
            uploadProgress.value[file.id] = uploadFile.progress || 0

            // Check for errors
            if (uploadFile.error) {
              uploadErrors.value.push({
                fileName: file.id,
                error:
                  uploadFile.error instanceof Error
                    ? uploadFile.error.message
                    : String(uploadFile.error)
              })
            } else if (uploadFile.result?.uploadError) {
              uploadErrors.value.push({
                fileName: file.id,
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
        console.error('❌ [AddPDF] Upload error:', uploadFile.error)
        uploadErrors.value.push({
          fileName: file.id,
          error:
            uploadFile.error instanceof Error
              ? uploadFile.error.message
              : String(uploadFile.error)
        })
      } else if (uploadFile?.result?.uploadError) {
        console.error('❌ [AddPDF] Upload result error:', uploadFile.result.uploadError)
        uploadErrors.value.push({
          fileName: file.id,
          error: uploadFile.result.uploadError
        })
      } else if (uploadFile?.result?.blobId) {
        console.log('✅ [AddPDF] Upload successful!', {
          fileId: file.id,
          fileName: file.file.name,
          blobId: uploadFile.result.blobId
        })
        uploadProgress.value[file.id] = 100
      }
    }
  } catch (error) {
    console.error('❌ [AddPDF] Upload exception:', error)
    const errorMsg = error instanceof Error ? error.message : 'Upload failed'
    uploadErrors.value.push({ fileName: 'Upload', error: errorMsg })
  }

  isUploading.value = false

  // If all files uploaded successfully, show success message
  if (uploadErrors.value.length === 0) {
    // Count successful uploads
    uploadSuccessCount.value = selectedFiles.value.filter((file) => {
      const uploadFile = uploadResults[file.id]
      return uploadFile?.result?.blobId
    }).length
  } else {
    uploadSuccessCount.value = 0
  }
}

const goToProject = () => {
  console.log('[AddPDF] Navigating to project:', projectId.value)
  // Clear Apollo cache for project PDFs to force refetch
  try {
    apolloClient.cache.evict({
      fieldName: 'blobs',
      args: {
        projectId: projectId.value
      }
    })
    apolloClient.cache.gc()
    console.log('[AddPDF] Cache cleared for project:', projectId.value)
  } catch (error) {
    console.warn('[AddPDF] Cache eviction failed:', error)
  }

  const targetRoute = projectRoute(projectId.value)
  console.log('[AddPDF] Target route:', targetRoute)
  router.push(targetRoute).catch((error) => {
    console.error('[AddPDF] Navigation failed:', error)
  })
}

const resetUpload = () => {
  selectedFiles.value = []
  uploadErrors.value = []
  uploadProgress.value = {}
  uploadSuccessCount.value = 0
}

const cancel = () => {
  router.push(projectRoute(projectId.value))
}
</script>
