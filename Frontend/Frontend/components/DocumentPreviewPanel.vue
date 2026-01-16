<template>
  <div class="doc-panel">
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
  token?: string
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

const { documentState, ensureDocumentState } = useDocumentWorkflow()
const config = useRuntimeConfig()

const containerId = `onlyoffice-editor-${Math.random().toString(36).slice(2, 10)}`
const loadState = ref<'idle' | 'loading' | 'ready' | 'error'>('idle')
const errorMessage = ref('')
const editorRef = shallowRef<OnlyOfficeEditorInstance | null>(null)
const lastLoadedKey = ref<string>('')
const lastSignedToken = ref<string>('')
const lastSignedConfig = ref<Record<string, unknown> | null>(null)

function makeDocumentKey(source: string) {
  const cleaned = source.replace(/[^0-9A-Za-z_.=-]/g, '_')
  return cleaned.slice(0, 127) || `doc-${Date.now()}`
}

const docTitle = computed(() => documentState.value?.title || 'Untitled Document')
const serverUrl = computed(() => (config.public.onlyofficeServerUrl as string | undefined)?.replace(/\/$/, '') || '')
const documentUrl = computed(() => {
  const doc = documentState.value || undefined
  const raw =
    (doc?.docUrl as string | undefined) ||
    (doc?.onlyoffice?.docUrl as string | undefined) ||
    (doc?.metadata?.docUrl as string | undefined) ||
    (config.public.onlyofficeDocumentUrl as string | undefined) ||
    ''

  // Base that the OnlyOffice server can reach; prefer explicit override
  const preferredBase =
    (config.public.onlyofficeDocumentBaseUrl as string | undefined)?.replace(/\/$/, '') ||
    (config.public.orchestratorUrl as string | undefined)?.replace(/\/$/, '') ||
    (typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : '')

  if (raw && raw.startsWith('/')) {
    const normalized = `${preferredBase}${raw}`
    console.log('📄 [OnlyOffice] Normalized relative docUrl to absolute:', normalized)
    return normalized
  }

  // If absolute but host differs and an explicit base is provided, rebase to the preferred host
  try {
    if (raw && preferredBase) {
      const urlObj = new URL(raw)
      const preferredObj = new URL(preferredBase)
      if (urlObj.host !== preferredObj.host) {
        const rebased = `${preferredBase}${urlObj.pathname}${urlObj.search}${urlObj.hash}`
        console.log('📄 [OnlyOffice] Rebased docUrl to preferred host:', rebased)
        return rebased
      }
    }
  } catch {
    // Ignore URL parsing errors
  }

  return raw
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
  const base =
    doc?.documentKey ||
    doc?.onlyoffice?.documentKey ||
    (doc?.metadata?.documentKey as string | undefined) ||
    (documentUrl.value ? `${documentUrl.value}-${doc?.version || 'v1'}` : `${docTitle.value}-v${doc?.version || 1}`)
  return makeDocumentKey(base || `doc-${Date.now()}`)
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

const overlayTitle = computed(() => {
  if (loadState.value === 'loading') return 'Launching Word editor…'
  if (loadState.value === 'error') return 'Unable to load the document'
  return 'Preparing editor…'
})

function resolveOnlyOfficeSignUrls(): string[] {
  const urls = new Set<string>()
  const override = (config.public.onlyofficeSignUrl as string | undefined)?.trim()
  if (override) {
    urls.add(override.replace(/\/$/, ''))
  }

  const orchestratorBase = (config.public.orchestratorUrl as string | undefined)?.replace(/\/$/, '')
  const browserOrigin = typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : ''
  const docOrigin = (() => {
    try {
      return documentUrl.value ? new URL(documentUrl.value).origin.replace(/\/$/, '') : ''
    } catch {
      return ''
    }
  })()
  const callbackOrigin = (() => {
    try {
      return callbackUrl.value ? new URL(callbackUrl.value).origin.replace(/\/$/, '') : ''
    } catch {
      return ''
    }
  })()

  if (orchestratorBase) {
    urls.add(`${orchestratorBase}/onlyoffice/sign`)
    urls.add(`${orchestratorBase}/api/onlyoffice/sign`)
  } else if (browserOrigin) {
    urls.add(`${browserOrigin}/onlyoffice/sign`)
    urls.add(`${browserOrigin}/api/onlyoffice/sign`)
  }

  if (docOrigin) {
    urls.add(`${docOrigin}/onlyoffice/sign`)
    urls.add(`${docOrigin}/api/onlyoffice/sign`)
  }
  if (callbackOrigin && callbackOrigin !== docOrigin) {
    urls.add(`${callbackOrigin}/onlyoffice/sign`)
    urls.add(`${callbackOrigin}/api/onlyoffice/sign`)
  }

  return Array.from(urls)
}

function destroyEditor() {
  if (editorRef.value?.destroyEditor) {
    editorRef.value.destroyEditor()
  }
  editorRef.value = null
}

async function signOnlyOfficeConfig(configToSign: OnlyOfficeEditorConfig): Promise<string | null> {
  const signUrls = resolveOnlyOfficeSignUrls()
  if (!signUrls.length) {
    throw new Error('Orchestrator URL is not configured for OnlyOffice signing.')
  }
  const payload = { config: configToSign }
  console.log('📄 [OnlyOffice] Signing payload (unsigned):', payload)

  const errors: string[] = []
  for (const url of signUrls) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) {
        const text = await response.text()
        errors.push(`${url} -> ${response.status}: ${text}`)
        continue
      }
      const data = (await response.json()) as { token?: string | null; unsigned?: boolean }
      if (!data.token) {
        if (data.unsigned) {
          console.warn(`📄 [OnlyOffice] Using unsigned editor config from ${url} (no JWT secret configured)`)
          lastSignedToken.value = ''
          lastSignedConfig.value = JSON.parse(JSON.stringify(configToSign))
          return null
        }
        errors.push(`${url} -> missing token`)
        continue
      }
      lastSignedToken.value = data.token
      lastSignedConfig.value = JSON.parse(JSON.stringify(configToSign))
      return data.token
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      errors.push(`${url} -> ${message}`)
    }
  }

  const errorHint = errors.length ? errors.join(' ; ') : 'Unknown error'
  throw new Error(`OnlyOffice sign failed (tried ${signUrls.length} endpoint${signUrls.length > 1 ? 's' : ''}): ${errorHint}`)
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
    console.log('📄 [OnlyOffice] Boot editor with:', {
      serverUrl: serverUrl.value,
      documentUrl: documentUrl.value,
      documentKey: documentKey.value,
      callbackUrl: callbackUrl.value,
      title: docTitle.value
    })
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
          console.error('📄 [OnlyOffice] Editor error', {
            event,
            serverUrl: serverUrl.value,
            documentUrl: documentUrl.value,
            documentKey: documentKey.value,
            callbackUrl: callbackUrl.value,
            title: docTitle.value
          })
          errorMessage.value = event?.data || 'OnlyOffice editor error'
          loadState.value = 'error'
        }
      },
      width: '100%',
      height: '100%'
    }

    console.log('📄 [OnlyOffice] Unsigned editorConfig:', editorConfig)

    // Request a signed JWT for this config from the orchestrator to satisfy OnlyOffice JWT validation
    const token = await signOnlyOfficeConfig(editorConfig)
    if (token) {
      editorConfig.token = token
    } else {
      delete (editorConfig as any).token
    }

    console.log('📄 [OnlyOffice] Signed editorConfig token:', token)
    editorRef.value = new api.DocEditor(containerId, editorConfig)
    lastLoadedKey.value = documentKey.value
  } catch (error: unknown) {
    console.error('Failed to launch OnlyOffice editor', error)
    const message = error instanceof Error ? error.message : String(error)
    errorMessage.value = message || 'Unable to load OnlyOffice editor.'
    loadState.value = 'error'
  }
}

watch(
  documentUrl,
  next => {
    if (!next) return
    console.log('📄 [OnlyOffice] documentUrl changed:', next)
    if (typeof window !== 'undefined') {
      ;(window as any).__onlyofficeDoc = {
        url: next,
        key: documentKey.value,
        serverUrl: serverUrl.value,
        callbackUrl: callbackUrl.value,
        title: docTitle.value
      }
    }
  },
  { immediate: true }
)

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
  background: #05060a;
  color: #f5f6fb;
}

.doc-body {
  flex: 1;
  position: relative;
}

.doc-editor {
  position: relative;
  height: 100%;
  overflow: hidden;
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
