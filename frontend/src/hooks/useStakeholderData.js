import { useCallback, useEffect, useState } from 'react'
import {
  fetchStakeholders,
  fetchStakeholderDetail,
  fetchStakeholderAnalytics,
  fetchStakeholderContracts,
  fetchStakeholderEmails,
  fetchStakeholderStats,
  fetchDepartmentStats,
  fetchStakeholderPerformance,
  fetchStakeholderNetwork,
  fetchFullCommunicationNetwork,
  fetchStakeholderRankings,
  fetchWorkloadBalance,
  fetchAnalyticsComparison,
  fetchDepartmentAnalytics,
} from '../api/stakeholders'

export function useStakeholders(filters = {}) {
  const [stakeholders, setStakeholders] = useState([])
  const [stats, setStats] = useState(null)
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [list, statsData, deptData] = await Promise.all([
        fetchStakeholders(filters),
        fetchStakeholderStats(),
        fetchDepartmentStats(),
      ])
      setStakeholders(list)
      setStats(statsData)
      setDepartments(deptData)
    } catch (err) {
      setError(err.message || 'Failed to load stakeholders')
    } finally {
      setLoading(false)
    }
  }, [filters.department, filters.role, filters.is_internal])

  useEffect(() => {
    load()
  }, [load])

  return { stakeholders, stats, departments, loading, error, refresh: load }
}

export function useStakeholderDetail(id) {
  const [detail, setDetail] = useState(null)
  const [contracts, setContracts] = useState([])
  const [emails, setEmails] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [network, setNetwork] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const [detailData, contractData, emailData, analyticsData] = await Promise.all([
        fetchStakeholderDetail(id),
        fetchStakeholderContracts(id),
        fetchStakeholderEmails(id),
        fetchStakeholderAnalytics(id),
      ])
      setDetail(detailData)
      setContracts(contractData)
      setEmails(emailData)
      setAnalytics(analyticsData)

      // Load performance and network separately (may fail for new stakeholders)
      try {
        const [perfData, networkData] = await Promise.all([
          fetchStakeholderPerformance(id),
          fetchStakeholderNetwork(id),
        ])
        setPerformance(perfData)
        setNetwork(networkData)
      } catch {
        // Non-critical data
      }
    } catch (err) {
      setError(err.message || 'Failed to load stakeholder details')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  return { detail, contracts, emails, analytics, performance, network, loading, error, refresh: load }
}

export function useCommunicationNetwork() {
  const [network, setNetwork] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchFullCommunicationNetwork()
      setNetwork(data)
    } catch (err) {
      setError(err.message || 'Failed to load communication network')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { network, loading, error, refresh: load }
}

export function useStakeholderComparison(ids) {
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!ids || ids.length < 2) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAnalyticsComparison(ids)
      setComparison(data)
    } catch (err) {
      setError(err.message || 'Failed to load comparison')
    } finally {
      setLoading(false)
    }
  }, [ids?.join(',')])

  useEffect(() => {
    load()
  }, [load])

  return { comparison, loading, error, refresh: load }
}

export function useStakeholderAnalyticsSummary() {
  const [rankings, setRankings] = useState([])
  const [workload, setWorkload] = useState(null)
  const [deptAnalytics, setDeptAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [rankData, workloadData, deptData] = await Promise.all([
        fetchStakeholderRankings('response_time', 'asc', 10),
        fetchWorkloadBalance(),
        fetchDepartmentAnalytics(),
      ])
      setRankings(rankData)
      setWorkload(workloadData)
      setDeptAnalytics(deptData)
    } catch (err) {
      setError(err.message || 'Failed to load stakeholder analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { rankings, workload, deptAnalytics, loading, error, refresh: load }
}
