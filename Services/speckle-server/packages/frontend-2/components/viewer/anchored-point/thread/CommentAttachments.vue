<template>
  <div>
    <div v-if="attachmentList.length > 0" class="flex flex-col gap-y-1 pt-2">
      <button
        v-for="attachment in attachmentList"
        :key="attachment.id"
        class="text-foreground hover:text-foreground-2 flex items-center gap-x-1"
        @click="() => onAttachmentClick(attachment)"
      >
        <Paperclip class="size-3" />
        <span class="truncate relative text-body-3xs">
          {{ attachment.fileName }}
        </span>
      </button>
    </div>

    <LayoutDialog v-model:open="dialogOpen" max-width="lg" :buttons="dialogButtons">
      <template #header>
        {{ dialogAttachment ? dialogAttachment.fileName : 'Attachment' }}
      </template>
      <template v-if="dialogAttachment">
        <div class="flex flex-col space-y-2 h-[600px]">
          <div
            v-if="dialogAttachmentError"
            class="flex justify-center items-center h-full"
          >
            <span class="inline-flex space-x-2 items-center">
              Failed to load attachment preview
            </span>
          </div>
          <template v-else-if="isImage(dialogAttachment) && dialogAttachmentObjectUrl">
            <div class="flex justify-center overflow-auto bg-foundation-3 p-4">
              <img
                :src="dialogAttachmentObjectUrl"
                alt="Attachment preview"
                class="max-w-full max-h-full"
              />
            </div>
          </template>
          <template v-else-if="isPDF(dialogAttachment) && dialogAttachmentObjectUrl">
            <PdfViewer :url="dialogAttachmentObjectUrl" />
          </template>
          <template v-else-if="isExcel(dialogAttachment) && dialogAttachmentObjectUrl">
            <ExcelViewer :url="dialogAttachmentObjectUrl" />
          </template>
          <template v-else>
            <div class="flex justify-center items-center h-full">
              <span class="inline-flex space-x-4 items-center">
                <TriangleAlert class="w-6 h-6" />
                <span>
                  Please note: This file is user-uploaded and has not been scanned for
                  security. Download at your own discretion.
                </span>
              </span>
            </div>
          </template>
        </div>
      </template>
    </LayoutDialog>
  </div>
</template>

<script setup lang="ts">
import type { Get } from 'type-fest'
import { ensureError } from '@speckle/shared'
import type { Nullable, Optional } from '@speckle/shared'
import { graphql } from '~~/lib/common/generated/gql'
import type { ThreadCommentAttachmentFragment } from '~~/lib/common/generated/gql/graphql'
import { prettyFileSize } from '~~/lib/core/helpers/file'
import { useFileDownload } from '~~/lib/core/composables/fileUpload'
import { ToastNotificationType, useGlobalToast } from '~~/lib/common/composables/toast'
import type { LayoutDialogButton } from '@speckle/ui-components'
import { Download, Paperclip, TriangleAlert } from 'lucide-vue-next'
import PdfViewer from '~/components/file-viewers/PdfViewer.vue'
import ExcelViewer from '~/components/file-viewers/ExcelViewer.vue'

type AttachmentFile = NonNullable<
  Get<ThreadCommentAttachmentFragment, 'text.attachments[0]'>
>

graphql(`
  fragment ThreadCommentAttachment on Comment {
    text {
      attachments {
        id
        fileName
        fileType
        fileSize
      }
    }
  }
`)

const props = defineProps<{
  attachments: ThreadCommentAttachmentFragment
  projectId: string
}>()

const { getBlobUrl, download } = useFileDownload()
const { triggerNotification } = useGlobalToast()

const dialogOpen = ref(false)
const dialogAttachment = ref(null as Nullable<AttachmentFile>)
const dialogAttachmentError = ref(null as Nullable<Error>)
const dialogAttachmentObjectUrl = ref(null as Nullable<string>)

const isImage = (attachment: AttachmentFile) => {
  switch (attachment.fileType) {
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
      return true
    default:
      return false
  }
}

const isPDF = (attachment: AttachmentFile) => {
  return attachment.fileType === 'pdf'
}

const isExcel = (attachment: AttachmentFile) => {
  return ['xlsx', 'xls'].includes(attachment.fileType)
}

const onAttachmentClick = (attachment: AttachmentFile) => {
  dialogAttachment.value = attachment
  dialogOpen.value = true
}

const onDownloadClick = async () => {
  if (!dialogAttachment.value) return

  try {
    const { id, fileName } = dialogAttachment.value
    await download({ blobId: id, fileName, projectId: props.projectId })
  } catch (e) {
    triggerNotification({
      type: ToastNotificationType.Danger,
      title: 'Download failed',
      description: ensureError(e).message
    })
  }
}

const attachmentList = computed(() => props.attachments?.text?.attachments || [])

const dialogButtons = computed((): Optional<LayoutDialogButton[]> => {
  if (!dialogAttachment.value) return undefined

  const button: LayoutDialogButton = {
    text: dialogAttachment.value.fileSize
      ? prettyFileSize(dialogAttachment.value.fileSize)
      : 'Download',
    props: {
      iconLeft: Download,
      color: 'outline'
    },
    onClick: () => {
      onDownloadClick()
    }
  }

  return [button]
})

watch(dialogOpen, (newIsOpen) => {
  if (!newIsOpen) {
    dialogAttachmentError.value = null

    if (dialogAttachmentObjectUrl.value) {
      URL.revokeObjectURL(dialogAttachmentObjectUrl.value)
      dialogAttachmentObjectUrl.value = null
    }
  } else if (dialogAttachment.value) {
    if (
      isImage(dialogAttachment.value) ||
      isPDF(dialogAttachment.value) ||
      isExcel(dialogAttachment.value)
    ) {
      getBlobUrl({ blobId: dialogAttachment.value.id, projectId: props.projectId })
        .then((url) => {
          dialogAttachmentObjectUrl.value = url
        })
        .catch((err) => {
          dialogAttachmentError.value = ensureError(err)
        })
    }
  }
})
</script>
