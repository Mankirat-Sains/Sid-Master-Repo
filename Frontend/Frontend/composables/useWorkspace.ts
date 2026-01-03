/**
 * Workspace State Management
 * Manages what's currently displayed in the middle panel (PDF, draft, model, etc.)
 * Uses a singleton pattern so all components share the same workspace state
 */

import { ref, readonly } from 'vue'

export type WorkspaceMode = 'empty' | 'pdf' | 'draft' | 'model' | 'spreadsheet'

export interface WorkspaceState {
  mode: WorkspaceMode
  pdfUrl?: string
  pdfFileName?: string
  draftTitle?: string
  draftContent?: string
  modelUrl?: string
  modelName?: string
}

// Shared state singleton
const sharedState = ref<WorkspaceState>({
  mode: 'empty'
})

export const useWorkspace = () => {
  const state = sharedState

  function openPDF(url: string, fileName?: string) {
    // Files in public/ folder are served at the root, so /writing/file.pdf works
    // If it's already a URL (http/https) or a public path (starts with /), use as-is
    // Otherwise, assume it's a public folder path
    let pdfUrl = url
    
    if (url.startsWith('http://') || url.startsWith('https://')) {
      // Already a full URL, use as-is
      pdfUrl = url
    } else if (url.startsWith('/')) {
      // Public folder path (e.g., /writing/file.pdf), use as-is
      pdfUrl = url
    } else if (url.includes(':') && !url.startsWith('file://')) {
      // Absolute file path (e.g., /Users/...), not supported in browser
      // Convert to public path if possible, otherwise show error
      console.warn('Absolute file paths are not supported. Use public folder paths instead.')
      pdfUrl = url
    }
    
    console.log('Opening PDF:', { url, pdfUrl, fileName })
    
    state.value = {
      mode: 'pdf',
      pdfUrl: pdfUrl,
      pdfFileName: fileName
    }
  }

  function openDraft(title: string, initialContent?: string) {
    state.value = {
      mode: 'draft',
      draftTitle: title,
      draftContent: initialContent || ''
    }
  }

  function openModel(url: string, name?: string) {
    state.value = {
      mode: 'model',
      modelUrl: url,
      modelName: name
    }
  }

  function clear() {
    state.value = {
      mode: 'empty'
    }
  }

  function updateDraftContent(content: string) {
    if (state.value.mode === 'draft') {
      state.value.draftContent = content
    }
  }

  return {
    state: readonly(state),
    openPDF,
    openDraft,
    openModel,
    clear,
    updateDraftContent
  }
}

