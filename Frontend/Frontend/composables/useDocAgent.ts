/**
 * Composable for DOCX Service Agent operations.
 * Mirrors the Excel sync composable but targets /api/doc/* proxies.
 */

interface DocBlock {
  index: number
  type: 'paragraph' | 'heading'
  text: string
  style?: string | null
  level?: number | null
}

interface DocStructure {
  blocks: DocBlock[]
  paragraph_count?: number
}

interface DocOpenResponse {
  doc_id: string
  file_path: string
  structure: DocStructure
}

interface DocApplyResponse {
  doc_id: string
  file_path: string
  structure: DocStructure
  change_summary: string[]
}

interface DocHistoryEntry {
  event: string
  timestamp: string
  change_summary?: string[]
  file_path?: string
  target_path?: string
}

interface DocHistoryResponse {
  doc_id: string
  total: number
  history: DocHistoryEntry[]
}

export const useDocAgent = () => {
  const config = useRuntimeConfig()

  const base = `${config.public.orchestratorUrl}/api/doc`

  async function health(): Promise<Record<string, unknown>> {
    return await $fetch(`${base}/health`, { method: 'GET' })
  }

  async function openDoc(filePath: string, docId?: string): Promise<DocOpenResponse> {
    return await $fetch<DocOpenResponse>(`${base}/open`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: { file_path: filePath, doc_id: docId || null }
    })
  }

  async function applyOps(params: {
    doc_id?: string
    file_path?: string
    ops: Array<Record<string, unknown>>
    save_as?: string
  }): Promise<DocApplyResponse> {
    if (!params.doc_id && !params.file_path) {
      throw new Error('doc_id or file_path is required to apply ops')
    }
    return await $fetch<DocApplyResponse>(`${base}/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: params
    })
  }

  async function exportDoc(docId: string, targetPath?: string): Promise<Record<string, unknown>> {
    return await $fetch<Record<string, unknown>>(`${base}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: { doc_id: docId, target_path: targetPath || null }
    })
  }

  async function getHistory(docId: string, limit: number = 100): Promise<DocHistoryResponse> {
    return await $fetch<DocHistoryResponse>(`${base}/history`, {
      method: 'GET',
      params: { doc_id: docId, limit }
    })
  }

  return {
    health,
    openDoc,
    applyOps,
    exportDoc,
    getHistory
  }
}
