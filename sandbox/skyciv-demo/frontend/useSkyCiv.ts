/** Composable for SkyCiv API integration */
import { ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_SKYCIV_API_URL || 'http://localhost:8000'

export const useSkyCiv = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const listModels = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/models`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()
      return data.models || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    } finally {
      loading.value = false
    }
  }

  const analyzeModel = async (modelName: string, analysisType: string = 'linear') => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          analysis_type: analysisType,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `API error: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getModelInfo = async (modelName: string) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/model/${modelName}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      return await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    listModels,
    analyzeModel,
    getModelInfo,
  }
}

