import apiClient from './client'

// Thread APIs
export async function fetchThreads(page = 1, pageSize = 20) {
  const { data } = await apiClient.get('/api/threads', { params: { page, page_size: pageSize } })
  return data
}

export async function fetchThreadDetail(threadId) {
  const { data } = await apiClient.get(`/api/threads/${threadId}`)
  return data
}

export async function fetchThreadStats() {
  const { data } = await apiClient.get('/api/threads/stats')
  return data
}

export async function fetchThreadEmails(threadId) {
  const { data } = await apiClient.get(`/api/threads/${threadId}/emails`)
  return data
}

// Classification APIs
export async function fetchClassificationResults(filters = {}) {
  const params = {}
  if (filters.category) params.category = filters.category
  if (filters.email_type) params.email_type = filters.email_type
  if (filters.urgency) params.urgency = filters.urgency
  const { data } = await apiClient.get('/api/classification/results', { params })
  return data
}

export async function fetchClassificationStats() {
  const { data } = await apiClient.get('/api/classification/stats')
  return data
}

// Search APIs
export async function searchEmails(q, filters = {}) {
  const params = { q, ...filters }
  const { data } = await apiClient.get('/api/search/emails', { params })
  return data
}

export async function globalSearch(q, type = 'all', page = 1) {
  const { data } = await apiClient.get('/api/search', { params: { q, type, page } })
  return data
}

export async function fetchSearchSuggestions(q) {
  const { data } = await apiClient.get('/api/search/suggestions', { params: { q } })
  return data
}
