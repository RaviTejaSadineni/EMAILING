import apiClient from './client'

export async function fetchStakeholders(filters = {}) {
  const params = {}
  if (filters.department) params.department = filters.department
  if (filters.role) params.role = filters.role
  if (filters.is_internal !== undefined && filters.is_internal !== null) params.is_internal = filters.is_internal
  const { data } = await apiClient.get('/api/stakeholders', { params })
  return data
}

export async function fetchStakeholderDetail(id) {
  const { data } = await apiClient.get(`/api/stakeholders/${id}`)
  return data
}

export async function fetchStakeholderContracts(id) {
  const { data } = await apiClient.get(`/api/stakeholders/${id}/contracts`)
  return data
}

export async function fetchStakeholderEmails(id) {
  const { data } = await apiClient.get(`/api/stakeholders/${id}/emails`)
  return data
}

export async function fetchStakeholderAnalytics(id) {
  const { data } = await apiClient.get(`/api/stakeholders/${id}/analytics`)
  return data
}

export async function fetchStakeholderComparison(ids) {
  const { data } = await apiClient.get('/api/stakeholders/comparison', { params: { ids: ids.join(',') } })
  return data
}

export async function fetchStakeholderStats() {
  const { data } = await apiClient.get('/api/stakeholders/stats')
  return data
}

export async function fetchDepartmentStats() {
  const { data } = await apiClient.get('/api/stakeholders/departments')
  return data
}

// Stakeholder Analytics API
export async function fetchStakeholderPerformance(id) {
  const { data } = await apiClient.get(`/api/analytics/stakeholders/${id}/performance`)
  return data
}

export async function fetchStakeholderResponseTimeTrend(id, period = 'week') {
  const { data } = await apiClient.get(`/api/analytics/stakeholders/${id}/response-time-trend`, { params: { period } })
  return data
}

export async function fetchStakeholderNetwork(id) {
  const { data } = await apiClient.get(`/api/analytics/stakeholders/${id}/network`)
  return data
}

export async function fetchFullCommunicationNetwork() {
  const { data } = await apiClient.get('/api/analytics/stakeholders/communication-network')
  return data
}

export async function fetchStakeholderRankings(metric = 'response_time', order = 'asc', limit = 10) {
  const { data } = await apiClient.get('/api/analytics/stakeholders/rankings', { params: { metric, order, limit } })
  return data
}

export async function fetchWorkloadBalance() {
  const { data } = await apiClient.get('/api/analytics/stakeholders/workload-balance')
  return data
}

export async function fetchAnalyticsComparison(ids) {
  const { data } = await apiClient.get('/api/analytics/stakeholders/comparison', { params: { ids: ids.join(',') } })
  return data
}

export async function fetchDepartmentAnalytics() {
  const { data } = await apiClient.get('/api/analytics/stakeholders/departments')
  return data
}
