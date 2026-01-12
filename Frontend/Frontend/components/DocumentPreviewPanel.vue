<template>
  <div class="doc-panel">
    <header class="doc-header">
      <div class="doc-header__left">
        <div class="doc-badge" :class="badgeClass">
          <span class="dot" />
          <span>{{ workflowLabel }}</span>
        </div>
        <div>
          <p class="doc-title">{{ docTitle }}</p>
          <p class="doc-subtitle">
            <span v-if="serverUrl">OnlyOffice server · {{ serverUrl }}</span>
            <span v-else>Configure ONLYOFFICE_SERVER_URL to enable live editing</span>
          </p>
        </div>
      </div>

      <div class="doc-header__actions">
        <span class="doc-status" :class="statusClass">{{ statusLabel }}</span>
        <button v-if="documentUrl" class="ghost" type="button" @click="openDocumentUrl">
          Open source
        </button>
      </div>
    </header>

    <ClientOnly>
      <div class="doc-body">
        <div v-if="!serverUrl" class="doc-state">
          <p class="doc-state__title">OnlyOffice server not configured</p>
          <p class="doc-state__hint">
            Start a Document Server (e.g. Docker image) and set ONLYOFFICE_SERVER_URL. You can also
            provide a default doc URL via ONLYOFFICE_DOCUMENT_URL.
          </p>
        </div>
        <div v-else-if="!documentUrl" class="doc-state">
          <p class="doc-state__title">No document selected</p>
          <p class="doc-state__hint">
            Provide a doc URL in the document metadata (docUrl or onlyoffice.docUrl) or set
            ONLYOFFICE_DOCUMENT_URL for a default.
          </p>
        </div>
        <div v-else class="doc-editor">
          <div :id="containerId" class="doc-editor__frame" />
          <div v-if="loadState !== 'ready'" class="doc-overlay" :class="{ error: loadState === 'error' }">
            <div class="spinner" />
            <p class="doc-overlay__title">
              {{ overlayTitle }}
            </p>
            <p v-if="errorMessage" class="doc-overlay__hint">{{ errorMessage }}</p>
          </div>
        </div>
      </div>
      <template #fallback>
        <div class="doc-body">
          <div class="doc-state">
            <p class="doc-state__title">Preparing editor…</p>
          </div>
        </div>
      </template>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useDocumentWorkflow } from '~/composables/useDocumentWorkflow'

type OnlyOfficePermissions = { edit?: boolean; download?: boolean; print?: boolean }
type OnlyOfficeUser = { id?: string; name?: string }
type OnlyOfficeErrorEvent = { data?: string }
type OnlyOfficeEditorInstance = { destroyEditor: () => void }
type OnlyOfficeEditorConfig = {
  documentType: string
  document: {
    fileType: string
    key: string
    title: string
    url: string
    permissions: OnlyOfficePermissions
  }
  editorConfig: {
    mode: 'view' | 'edit'
    lang: string
    callbackUrl?: string
    user: OnlyOfficeUser
    customization: Record<string, unknown>
  }
  events: {
    onDocumentReady?: () => void
    onError?: (event: OnlyOfficeErrorEvent) => void
  }
  width: string
  height: string
}

declare global {
  interface Window {
    DocsAPI?: {
      DocEditor: new (elementId: string, config: OnlyOfficeEditorConfig) => OnlyOfficeEditorInstance
    }
  }
}

let apiLoader: Promise<void> | null = null
let apiLoaderHost = ''

function loadOnlyOfficeApi(serverUrl: string) {
  if (typeof window === 'undefined') return Promise.resolve()

  const normalized = serverUrl.replace(/\/$/, '')
  if (window.DocsAPI?.DocEditor && apiLoaderHost === normalized) return Promise.resolve()
  if (apiLoader && apiLoaderHost === normalized) return apiLoader

  apiLoaderHost = normalized
  apiLoader = null
  window.DocsAPI = undefined

  apiLoader = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `${normalized}/web-apps/apps/api/documents/api.js`
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load OnlyOffice API'))
    document.head.appendChild(script)
  })

  return apiLoader
}

const { documentState, activeWorkflowMode, ensureDocumentState } = useDocumentWorkflow()
const config = useRuntimeConfig()

const containerId = `onlyoffice-editor-${Math.random().toString(36).slice(2, 10)}`
const loadState = ref<'idle' | 'loading' | 'ready' | 'error'>('idle')
const errorMessage = ref('')
const editorRef = shallowRef<OnlyOfficeEditorInstance | null>(null)
const lastLoadedKey = ref<string>('')

const docTitle = computed(() => documentState.value?.title || 'Untitled Document')
const serverUrl = computed(() => (config.public.onlyofficeServerUrl as string | undefined)?.replace(/\/$/, '') || '')
const documentUrl = computed(() => {
  const doc = documentState.value || undefined
  return (
    (doc?.docUrl as string | undefined) ||
    (doc?.onlyoffice?.docUrl as string | undefined) ||
    (doc?.metadata?.docUrl as string | undefined) ||
    (config.public.onlyofficeDocumentUrl as string | undefined) ||
    ''
  )
})
const callbackUrl = computed(() => {
  const doc = documentState.value || undefined
  return (
    (doc?.callbackUrl as string | undefined) ||
    (doc?.onlyoffice?.callbackUrl as string | undefined) ||
    (doc?.metadata?.callbackUrl as string | undefined) ||
    (config.public.onlyofficeCallbackUrl as string | undefined) ||
    ''
  )
})
const documentKey = computed(() => {
  const doc = documentState.value || undefined
  return (
    doc?.documentKey ||
    doc?.onlyoffice?.documentKey ||
    (doc?.metadata?.documentKey as string | undefined) ||
    (documentUrl.value ? `${documentUrl.value}-${doc?.version || 'v1'}` : `${docTitle.value}-v${doc?.version || 1}`)
  )
})
const editorUser = computed<OnlyOfficeUser>(() => {
  const doc = documentState.value || undefined
  return {
    id: doc?.onlyoffice?.user?.id || (config.public.onlyofficeUserId as string | undefined) || 'user-1',
    name: doc?.onlyoffice?.user?.name || (config.public.onlyofficeUserName as string | undefined) || 'Current User'
  }
})
const permissions = computed<OnlyOfficePermissions>(() => {
  const doc = documentState.value || undefined
  return {
    edit: doc?.onlyoffice?.permissions?.edit ?? true,
    download: doc?.onlyoffice?.permissions?.download ?? true,
    print: doc?.onlyoffice?.permissions?.print ?? true
  }
})

const workflowLabel = computed(() => {
  if (activeWorkflowMode.value === 'desktop_agent') return 'Desktop Agent'
  if (activeWorkflowMode.value === 'docgen') return 'Doc Generation'
  return 'Document Editor'
})
const badgeClass = computed(() => (activeWorkflowMode.value === 'desktop_agent' ? 'desktop' : 'docgen'))
const statusLabel = computed(() => {
  if (!serverUrl.value) return 'Server missing'
  if (loadState.value === 'loading') return 'Connecting…'
  if (loadState.value === 'ready') return 'Editing live'
  if (loadState.value === 'error') return 'Load failed'
  return 'Idle'
})
const statusClass = computed(() => {
  if (!serverUrl.value || loadState.value === 'error') return 'state-error'
  if (loadState.value === 'ready') return 'state-ready'
  if (loadState.value === 'loading') return 'state-warn'
  return 'state-muted'
})
const overlayTitle = computed(() => {
  if (loadState.value === 'loading') return 'Launching Word editor…'
  if (loadState.value === 'error') return 'Unable to load the document'
  return 'Preparing editor…'
})

function openDocumentUrl() {
  if (!documentUrl.value || typeof window === 'undefined') return
  window.open(documentUrl.value, '_blank', 'noopener,noreferrer')
}

function destroyEditor() {
  if (editorRef.value?.destroyEditor) {
    editorRef.value.destroyEditor()
  }
  editorRef.value = null
}

async function bootEditor() {
  if (typeof window === 'undefined') return
  if (!serverUrl.value) {
    loadState.value = 'error'
    errorMessage.value = 'Set ONLYOFFICE_SERVER_URL to load the editor.'
    destroyEditor()
    return
  }
  if (!documentUrl.value) {
    loadState.value = 'error'
    errorMessage.value = 'No document URL provided for OnlyOffice.'
    destroyEditor()
    return
  }
  if (lastLoadedKey.value === documentKey.value && loadState.value === 'ready') return

  loadState.value = 'loading'
  errorMessage.value = ''

  try {
    await loadOnlyOfficeApi(serverUrl.value)
    destroyEditor()

    const api = window.DocsAPI
    const container = document.getElementById(containerId)
    if (!api?.DocEditor || !container) {
      throw new Error('OnlyOffice client failed to initialize')
    }

    const editorConfig: OnlyOfficeEditorConfig = {
      documentType: 'word',
      document: {
        fileType: 'docx',
        key: documentKey.value,
        title: docTitle.value.endsWith('.docx') ? docTitle.value : `${docTitle.value}.docx`,
        url: documentUrl.value,
        permissions: permissions.value
      },
      editorConfig: {
        mode: permissions.value.edit ? 'edit' : 'view',
        lang: 'en',
        callbackUrl: callbackUrl.value || undefined,
        user: editorUser.value,
        customization: {
          uiTheme: 'theme-dark',
          compactToolbar: false,
          toolbarNoTabs: false,
          autosave: true,
          forcesave: true,
          feedback: false,
          hideRightMenu: false
        }
      },
      events: {
        onDocumentReady: () => {
          loadState.value = 'ready'
        },
        onError: (event: OnlyOfficeErrorEvent) => {
          console.error('OnlyOffice editor error', event)
          errorMessage.value = event?.data || 'OnlyOffice editor error'
          loadState.value = 'error'
        }
      },
      width: '100%',
      height: '100%'
    }

    editorRef.value = new api.DocEditor(containerId, editorConfig)
    lastLoadedKey.value = documentKey.value
  } catch (error: unknown) {
    console.error('Failed to launch OnlyOffice editor', error)
    const message = error instanceof Error ? error.message : String(error)
    errorMessage.value = message || 'Unable to load OnlyOffice editor.'
    loadState.value = 'error'
  }
}

onMounted(() => {
  ensureDocumentState()
  void bootEditor()
})

watch(
  () => [serverUrl.value, documentUrl.value, documentKey.value, callbackUrl.value],
  () => {
    void bootEditor()
  }
)

onBeforeUnmount(() => {
  destroyEditor()
})
</script>

<style scoped>
.doc-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: radial-gradient(140% 140% at 20% 20%, rgba(89, 64, 255, 0.12), transparent),
    linear-gradient(180deg, #0b0c12 0%, #05060a 100%);
  color: #f5f6fb;
  border-left: 1px solid rgba(255, 255, 255, 0.05);
}

.doc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(11, 12, 18, 0.75);
  backdrop-filter: blur(10px);
}

.doc-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.doc-badge .dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  display: inline-block;
  background: currentColor;
  box-shadow: 0 0 10px currentColor;
}

.doc-badge.desktop {
  color: #c7f9cc;
  background: rgba(69, 180, 112, 0.15);
  border-color: rgba(69, 180, 112, 0.35);
}

.doc-badge.docgen {
  color: #d3c7ff;
  background: rgba(117, 90, 255, 0.18);
  border-color: rgba(117, 90, 255, 0.35);
}

.doc-title {
  font-size: 17px;
  font-weight: 800;
  margin: 0;
}

.doc-subtitle {
  margin: 2px 0 0 0;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
}

.doc-header__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.doc-status {
  padding: 6px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.doc-status.state-ready {
  color: #b5ffcf;
  background: rgba(69, 180, 112, 0.14);
  border-color: rgba(69, 180, 112, 0.35);
}

.doc-status.state-warn {
  color: #ffe7b2;
  background: rgba(255, 193, 79, 0.16);
  border-color: rgba(255, 193, 79, 0.35);
}

.doc-status.state-error {
  color: #ffc9c9;
  background: rgba(255, 99, 110, 0.18);
  border-color: rgba(255, 99, 110, 0.4);
}

.doc-status.state-muted {
  color: #d5ddff;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.14);
}

.ghost {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f5f5f7;
  border-radius: 9999px;
  padding: 7px 12px;
  font-size: 12px;
  transition: all 0.15s ease;
}

.ghost:hover {
  background: rgba(255, 255, 255, 0.12);
}

.doc-body {
  flex: 1;
  position: relative;
  padding: 14px;
}

.doc-editor {
  position: relative;
  height: 100%;
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(25, 27, 37, 0.95), rgba(12, 14, 20, 0.95));
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 14px 48px rgba(0, 0, 0, 0.45);
}

.doc-editor__frame {
  position: absolute;
  inset: 0;
}

.doc-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(180deg, rgba(8, 9, 14, 0.9), rgba(8, 9, 14, 0.95));
  text-align: center;
  padding: 24px;
  z-index: 2;
}

.doc-overlay.error {
  background: linear-gradient(180deg, rgba(28, 8, 10, 0.92), rgba(17, 6, 7, 0.96));
}

.doc-overlay__title {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.doc-overlay__hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  max-width: 520px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: #9f7aea;
  border-radius: 9999px;
  animation: spin 1s linear infinite;
}

.doc-state {
  height: 100%;
  border-radius: 18px;
  border: 1px dashed rgba(255, 255, 255, 0.16);
  background: rgba(15, 15, 24, 0.75);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 24px;
  gap: 8px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.doc-state__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.doc-state__hint {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  max-width: 560px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
