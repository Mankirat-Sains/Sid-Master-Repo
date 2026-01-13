import { computed, ref } from 'vue'
import { useRuntimeConfig } from '#app'

export type WorkflowMode = 'default' | 'desktop_agent' | 'docgen'

export type DocumentBlockType = 'heading' | 'paragraph' | 'list' | 'table' | 'quote' | 'code' | 'callout'

export interface DocumentBlock {
  id: string
  type: DocumentBlockType
  text?: string
  level?: number
  items?: string[]
  rows?: string[][]
  style?: {
    bold?: boolean
    italic?: boolean
    underline?: boolean
    align?: 'left' | 'center' | 'right'
    highlight?: boolean
  }
  children?: DocumentBlock[]
}

export interface DocumentSection {
  id: string
  title?: string
  blocks: DocumentBlock[]
}

export interface PdfState {
  url?: string
  page?: number
  totalPages?: number
}

export interface OnlyOfficeConfig {
  docUrl?: string
  callbackUrl?: string
  documentKey?: string
  fileType?: 'docx' | 'doc'
  user?: {
    id?: string
    name?: string
  }
  permissions?: {
    edit?: boolean
    download?: boolean
    print?: boolean
  }
}

export interface StructuredDocument {
  title?: string
  summary?: string
  metadata?: Record<string, unknown>
  sections: DocumentSection[]
  docType?: 'docx' | 'pdf'
  pdf?: PdfState
  zoom?: number
  viewMode?: 'preview' | 'edit'
  version: number
  lastEditedId?: string
  html?: string
  docUrl?: string
  callbackUrl?: string
  documentKey?: string
  onlyoffice?: OnlyOfficeConfig
}

const activeWorkflowMode = ref<WorkflowMode>('default')
const documentState = ref<StructuredDocument | null>(null)

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 8)}-${Date.now()}`
}

function getDocumentBaseUrl() {
  const config = useRuntimeConfig()
  const configuredBase = (config.public.onlyofficeDocumentBaseUrl as string | undefined)?.trim()
  if (configuredBase) {
    return configuredBase.replace(/\/$/, '')
  }
  const configuredDocUrl = (config.public.onlyofficeDocumentUrl as string | undefined)?.trim()
  if (configuredDocUrl && configuredDocUrl.includes('/documents/')) {
    return configuredDocUrl.split('/documents/')[0]?.replace(/\/$/, '') || ''
  }
  const orchestrator = (config.public.orchestratorUrl as string | undefined) || 'http://localhost:8000'
  return orchestrator.replace(/\/$/, '')
}

function buildDocumentIdentifiers(prefix: string) {
  const timestamp = Date.now()
  const randomId = Math.random().toString(36).slice(2, 8)
  return { timestamp, randomId, key: `${prefix}-${timestamp}-${randomId}` }
}

function normalizeSection(section: Partial<DocumentSection>, index: number): DocumentSection {
  const blocks = Array.isArray(section.blocks) ? section.blocks : []
  return {
    id: section.id || createId(`section-${index + 1}`),
    title: section.title || `Section ${index + 1}`,
    blocks: blocks.map((block, blockIdx) => normalizeBlock(block, index, blockIdx))
  }
}

function normalizeBlock(block: Partial<DocumentBlock>, sectionIndex: number, blockIndex: number): DocumentBlock {
  return {
    id: block.id || createId(`block-${sectionIndex + 1}-${blockIndex + 1}`),
    type: block.type || 'paragraph',
    text: block.text ?? '',
    level: block.level,
    items: block.items,
    rows: block.rows,
    style: block.style,
    children: block.children?.map((child, childIdx) => normalizeBlock(child, sectionIndex, childIdx))
  }
}

function normalizeDocument(doc: StructuredDocument): StructuredDocument {
  const sections = Array.isArray(doc.sections) && doc.sections.length ? doc.sections : [
    {
      id: createId('section'),
      title: 'Draft',
      blocks: [
        {
          id: createId('block'),
          type: 'paragraph',
          text: 'Document editing enabled. Ask Sid to add or change content.'
        }
      ]
    }
  ]

  return {
    title: doc.title || 'Untitled Document',
    summary: doc.summary,
    metadata: doc.metadata || {},
    docUrl: doc.docUrl || doc.metadata?.docUrl as string | undefined,
    callbackUrl: doc.callbackUrl || doc.metadata?.callbackUrl as string | undefined,
    documentKey: doc.documentKey || doc.metadata?.documentKey as string | undefined,
    onlyoffice: doc.onlyoffice || (doc.metadata?.onlyoffice as OnlyOfficeConfig | undefined),
    docType: doc.docType || (doc.pdf?.url ? 'pdf' : 'docx'),
    pdf: doc.pdf,
    zoom: doc.zoom ?? 1,
    viewMode: doc.viewMode || 'preview',
    sections: sections.map((section, idx) => normalizeSection(section, idx)),
    version: typeof doc.version === 'number' ? doc.version : 1,
    lastEditedId: doc.lastEditedId,
    html: doc.html
  }
}

function createEmptyDocument(): StructuredDocument {
  const { timestamp, randomId, key } = buildDocumentIdentifiers('blank')
  const baseUrl = getDocumentBaseUrl()
  const defaultDocUrl = `${baseUrl}/documents/blank.docx?t=${timestamp}&id=${randomId}`

  return normalizeDocument({
    title: 'Blank Document',
    docUrl: defaultDocUrl,
    documentKey: key,
    metadata: { docUrl: defaultDocUrl, documentKey: key },
    onlyoffice: { docUrl: defaultDocUrl, documentKey: key },
    sections: [
      {
        id: createId('section'),
        title: '',
        blocks: [
          {
            id: createId('block'),
            type: 'paragraph',
            text: ''
          }
        ]
      }
    ],
    version: 1,
    zoom: 1,
    viewMode: 'edit'
  })
}

function cloneDocumentState(doc: StructuredDocument | null): StructuredDocument | null {
  return doc ? JSON.parse(JSON.stringify(doc)) as StructuredDocument : null
}

export function normalizeWorkflow(raw?: string | null): WorkflowMode {
  if (!raw) return 'default'
  const value = raw.toLowerCase()
  if (value.includes('desktop')) return 'desktop_agent'
  if (value.includes('doc') || value.includes('document')) return 'docgen'
  return 'default'
}

function unwrapDocumentPayload(payload: any): Partial<StructuredDocument> | null {
  if (!payload) return null
  if (payload.doc_generation_result?.document) return payload.doc_generation_result.document
  if (payload.doc_generation_result?.document_state) return payload.doc_generation_result.document_state
  if (payload.document_state) return payload.document_state
  if (payload.document_patch) return payload.document_patch
  if (payload.document) return payload.document
  if (payload.doc_generation_result) return payload.doc_generation_result
  if (payload.doc) return payload.doc
  return payload
}

function deriveLastEditedId(patch: Partial<StructuredDocument>) {
  if (patch.lastEditedId) return patch.lastEditedId
  if (patch.sections?.length) {
    const lastSection = patch.sections[patch.sections.length - 1]
    if (lastSection.blocks?.length) {
      const lastBlock = lastSection.blocks[lastSection.blocks.length - 1]
      return lastBlock.id
    }
  }
  return undefined
}

function mergeDocument(base: StructuredDocument, patch: Partial<StructuredDocument>): StructuredDocument {
  const merged: StructuredDocument = {
    ...base,
    ...patch,
    metadata: { ...(base.metadata || {}), ...(patch.metadata || {}) },
    zoom: patch.zoom ?? base.zoom ?? 1,
    viewMode: patch.viewMode || base.viewMode || 'preview',
    pdf: patch.pdf ? { ...(base.pdf || {}), ...patch.pdf } : base.pdf,
    sections: patch.sections ? patch.sections.map((section, idx) => normalizeSection(section, idx)) : base.sections,
    version: (base.version || 0) + 1
  }

  merged.lastEditedId = deriveLastEditedId(patch) || merged.lastEditedId
  return merged
}

function ensureDocumentState(): StructuredDocument {
  if (!documentState.value) {
    documentState.value = createEmptyDocument()
  }
  return documentState.value
}

function setDocumentState(next: StructuredDocument | null) {
  documentState.value = next ? normalizeDocument(next) : null
}

function createDocumentFromAnswer(conversationId: string, answer: string) {
  const baseUrl = getDocumentBaseUrl()
  const { timestamp, randomId } = buildDocumentIdentifiers('conv')
  const safeConversationId = (conversationId || 'conversation').replace(/[^0-9A-Za-z_-]/g, '') || 'conversation'
  const docId = `conv-${safeConversationId}-${timestamp}`
  const docUrl = `${baseUrl}/documents/${docId}.docx?t=${timestamp}&id=${randomId}`
  const docKey = `${docId}-${randomId}`

  const doc = normalizeDocument({
    title: `Document ${safeConversationId}`,
    docUrl,
    documentKey: docKey,
    metadata: { docUrl, documentKey: docKey },
    onlyoffice: { docUrl, documentKey: docKey },
    sections: [
      {
        id: createId('section'),
        title: '',
        blocks: [
          {
            id: createId('block'),
            type: 'paragraph',
            text: answer || ''
          }
        ]
      }
    ],
    version: 1,
    viewMode: 'edit'
  })

  documentState.value = doc
  console.log('📄 [DocWorkflow] Created document from answer:', {
    conversationId: safeConversationId,
    url: docUrl,
    key: docKey,
    timestamp,
    randomId
  })
  return doc
}

function applyDocumentPatch(patchInput: any): StructuredDocument | null {
  const patch = unwrapDocumentPayload(patchInput)
  if (!patch) return documentState.value
  const base = ensureDocumentState()
  const merged = mergeDocument(base, patch)
  documentState.value = merged
  return merged
}

function updateZoom(nextZoom: number) {
  const base = ensureDocumentState()
  const zoom = Math.max(0.5, Math.min(2, nextZoom))
  documentState.value = { ...base, zoom, version: base.version + 1 }
}

function updateViewMode(mode: 'preview' | 'edit') {
  const base = ensureDocumentState()
  documentState.value = { ...base, viewMode: mode, version: base.version + 1 }
}

function updatePdfPage(page: number) {
  const base = ensureDocumentState()
  const pdf = base.pdf || {}
  documentState.value = { ...base, pdf: { ...pdf, page }, version: base.version + 1 }
}

function updatePdfMeta(meta: PdfState) {
  const base = ensureDocumentState()
  const pdf = base.pdf || {}
  documentState.value = {
    ...base,
    pdf: { ...pdf, ...meta },
    docType: 'pdf',
    version: base.version + 1
  }
}

function setWorkflowMode(mode: WorkflowMode) {
  activeWorkflowMode.value = mode
}

function resetDocumentWorkflow() {
  activeWorkflowMode.value = 'default'
  documentState.value = null
}

function resetToBlankDocument() {
  documentState.value = createEmptyDocument()
}

const isDocumentWorkflow = computed(() => ['desktop_agent', 'docgen'].includes(activeWorkflowMode.value))

export function useDocumentWorkflow() {
  return {
    activeWorkflowMode,
    documentState,
    isDocumentWorkflow,
    setWorkflowMode,
    setDocumentState,
    applyDocumentPatch,
    ensureDocumentState,
    resetDocumentWorkflow,
    resetToBlankDocument,
    createDocumentFromAnswer,
    updateZoom,
    updateViewMode,
    updatePdfPage,
    updatePdfMeta,
    cloneDocumentState
  }
}

export { cloneDocumentState }
