import apiClient from './client'

export async function fetchDashboardKPIs(filters = {}) {
  const params = {}
  if (filters.dateFrom) params.date_from = filters.dateFrom
  if (filters.dateTo) params.date_to = filters.dateTo
  if (filters.contractType) params.contract_type = filters.contractType
  if (filters.department) params.department = filters.department
  const { data } = await apiClient.get('/api/dashboard/kpis', { params })
  return data
}

export async function fetchTrend(type, params = {}) {
  const { data } = await apiClient.get(`/api/dashboard/trends/${type}`, { params })
  return data
}

export async function fetchDistribution(type) {
  const { data } = await apiClient.get(`/api/dashboard/distributions/${type}`)
  return data
}

export async function fetchTopBottlenecks(limit = 10) {
  const { data } = await apiClient.get('/api/dashboard/top/bottlenecks', { params: { limit } })
  return data
}

export async function fetchTopRisks(limit = 10) {
  const { data } = await apiClient.get('/api/dashboard/top/risks', { params: { limit } })
  return data
}

export async function fetchRecentActivity(limit = 20) {
  const { data } = await apiClient.get('/api/dashboard/recent-activity', { params: { limit } })
  return data
}

export async function fetchStageTransitions() {
  const { data } = await apiClient.get('/api/analytics/contracts/stage-transitions')
  return data
}

export async function fetchStageDurationStats() {
  const { data } = await apiClient.get('/api/analytics/contracts/stage-duration-stats')
  return data
}

export async function fetchContractTimeline(contractId) {
  const { data } = await apiClient.get(`/api/analytics/contracts/timeline/${contractId}`)
  return data
}

export async function fetchBottleneckAnalysis() {
  const { data } = await apiClient.get('/api/analytics/contracts/bottlenecks')
  return data
}

export async function fetchStageHealth() {
  const { data } = await apiClient.get('/api/analytics/contracts/stage-health')
  return data
}

export async function fetchVelocityTrend(period = 'week') {
  const { data } = await apiClient.get('/api/analytics/contracts/velocity-trend', { params: { period } })
  return data
}

export async function fetchCycleTimeDistribution() {
  const { data } = await apiClient.get('/api/analytics/contracts/cycle-time-distribution')
  return data
}
