import { useRuntimeConfig } from '#app'

interface UploadIFCResult {
  success: boolean
  speckle_project_id: string
  speckle_model_name: string
  message: string
}

export const useIFCUpload = () => {
  const config = useRuntimeConfig()

  async function uploadIFCFile(
    file: File,
    projectId?: string,
    modelName: string = 'main',
    onProgress?: (percentage: number) => void
  ): Promise<UploadIFCResult> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) {
      formData.append('project_id', projectId)
    }
    formData.append('model_name', modelName)

    return new Promise<UploadIFCResult>((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const percentage = (e.loaded / e.total) * 100
          onProgress(percentage)
        }
      })

      // Handle successful response
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText)
            resolve(result)
          } catch (e) {
            reject(new Error('Invalid response from server'))
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText)
            reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`))
          } catch {
            reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`))
          }
        }
      })

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'))
      })

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'))
      })

      // Start upload
      xhr.open('POST', `${config.public.orchestratorUrl}/chat/upload-ifc`)
      xhr.send(formData)
    })
  }

  return {
    uploadIFCFile
  }
}

