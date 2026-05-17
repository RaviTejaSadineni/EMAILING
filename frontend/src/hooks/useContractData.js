import { useCallback, useEffect, useState } from 'react'
import {
  fetchContracts,
  searchContracts,
  fetchContractStats,
  fetchContractDetail,
  fetchContractTimeline,
  fetchContractClauses,
  fetchContractStakeholders,
  startContractExtraction,
  fetchExtractionStatus,
} from '../api/contracts'

export function useContracts(filters = {}) {
  const [contracts, setContracts] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [list, statsData] = await Promise.all([
        fetchContracts(filters),
        fetchContractStats(),
      ])
      setContracts(list)
      setStats(statsData)
    } catch (err) {
      setError(err.message || 'Failed to load contracts')
    } finally {
      setLoading(false)
    }
  }, [filters.agreement_type, filters.counterparty, filters.stage, filters.min_risk_score, filters.max_risk_score])

  useEffect(() => {
    load()
  }, [load])

  return { contracts, stats, loading, error, refresh: load }
}

export function useContractDetail(contractId) {
  const [detail, setDetail] = useState(null)
  const [timeline, setTimeline] = useState(null)
  const [clauses, setClauses] = useState([])
  const [stakeholders, setStakeholders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!contractId) return
    setLoading(true)
    setError(null)
    try {
      const [detailData, timelineData, clauseData, stakeholderData] = await Promise.all([
        fetchContractDetail(contractId),
        fetchContractTimeline(contractId),
        fetchContractClauses(contractId),
        fetchContractStakeholders(contractId),
      ])
      setDetail(detailData)
      setTimeline(timelineData)
      setClauses(clauseData)
      setStakeholders(stakeholderData)
    } catch (err) {
      setError(err.message || 'Failed to load contract details')
    } finally {
      setLoading(false)
    }
  }, [contractId])

  useEffect(() => {
    load()
  }, [load])

  return { detail, timeline, clauses, stakeholders, loading, error, refresh: load }
}

export function useContractSearch() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (q) => {
    if (!q || !q.trim()) {
      setResults(null)
      return
    }
    setLoading(true)
    try {
      const data = await searchContracts(q)
      setResults(data)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(() => setResults(null), [])

  return { results, loading, search, clear }
}

export function useContractExtraction() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const start = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await startContractExtraction()
      setStatus(data)
    } catch (err) {
      setError(err.message || 'Failed to start extraction')
    } finally {
      setLoading(false)
    }
  }, [])

  const checkStatus = useCallback(async () => {
    try {
      const data = await fetchExtractionStatus()
      setStatus(data)
    } catch {
      // No job exists yet
    }
  }, [])

  return { status, loading, error, start, checkStatus }
}
