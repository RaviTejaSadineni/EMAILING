import apiClient from './client'
import { API_BASE_URL } from '../utils/constants'

export function uploadMbox(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE_URL}/imports/upload`)

    const token = localStorage.getItem('access_token')
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) {
        return
      }
      onProgress(Math.round((event.loaded / event.total) * 100))
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
        return
      }
      reject(new Error(xhr.responseText || 'Upload failed'))
    }

    xhr.onerror = () => reject(new Error('Network error during upload'))

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })
}

export async function uploadChunk(chunk, metadata) {
  const formData = new FormData()
  formData.append('file', chunk)
  formData.append('job_id', metadata.jobId)
  formData.append('chunk_number', metadata.chunkNumber)
  formData.append('total_chunks', metadata.totalChunks)
  const { data } = await apiClient.post('/imports/upload/chunk', formData)
  return data
}

export async function getImportJobs() {
  const { data } = await apiClient.get('/imports/jobs')
  return data
}

export async function getImportJob(id) {
  const { data } = await apiClient.get(`/imports/jobs/${id}`)
  return data
}

export async function cancelImport(id) {
  const { data } = await apiClient.post(`/imports/jobs/${id}/cancel`)
  return data
}

export async function retryImport(id) {
  const { data } = await apiClient.post(`/imports/jobs/${id}/retry`)
  return data
}

export async function getImportStats() {
  const { data } = await apiClient.get('/imports/stats')
  return data
}
