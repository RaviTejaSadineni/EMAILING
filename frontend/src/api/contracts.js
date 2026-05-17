import apiClient from './client'

export async function fetchContracts(filters = {}) {
  const params = {}
  if (filters.agreement_type) params.agreement_type = filters.agreement_type
  if (filters.counterparty) params.counterparty = filters.counterparty
  if (filters.stage) params.stage = filters.stage
  if (filters.min_risk_score != null) params.min_risk_score = filters.min_risk_score
  if (filters.max_risk_score != null) params.max_risk_score = filters.max_risk_score
  const { data } = await apiClient.get('/api/contracts', { params })
  return data
}

export async function searchContracts(q) {
  const { data } = await apiClient.get('/api/contracts/search', { params: { q } })
  return data
}

export async function fetchContractStats() {
  const { data } = await apiClient.get('/api/contracts/stats')
  return data
}

export async function fetchContractDetail(contractId) {
  const { data } = await apiClient.get(`/api/contracts/${contractId}`)
  return data
}

export async function fetchContractTimeline(contractId) {
  const { data } = await apiClient.get(`/api/contracts/${contractId}/timeline`)
  return data
}

export async function fetchContractClauses(contractId) {
  const { data } = await apiClient.get(`/api/contracts/${contractId}/clauses`)
  return data
}

export async function fetchContractStakeholders(contractId) {
  const { data } = await apiClient.get(`/api/contracts/${contractId}/stakeholders`)
  return data
}

export async function startContractExtraction() {
  const { data } = await apiClient.post('/api/contracts/start-extraction')
  return data
}

export async function fetchExtractionStatus() {
  const { data } = await apiClient.get('/api/contracts/status')
  return data
}
