import { useCallback, useEffect, useState } from 'react'
import {
  fetchThreads,
  fetchThreadDetail,
  fetchThreadStats,
  fetchClassificationResults,
  fetchClassificationStats,
  searchEmails,
} from '../api/emails'

export function useThreads(page = 1, pageSize = 20) {
  const [threads, setThreads] = useState([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [listData, statsData] = await Promise.all([
        fetchThreads(page, pageSize),
        fetchThreadStats(),
      ])
      setThreads(listData.items || [])
      setTotal(listData.total || 0)
      setStats(statsData)
    } catch (err) {
      setError(err.message || 'Failed to load threads')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize])

  useEffect(() => {
    load()
  }, [load])

  return { threads, total, stats, loading, error, refresh: load }
}

export function useThreadDetail(threadId) {
  const [thread, setThread] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!threadId) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchThreadDetail(threadId)
      setThread(data)
    } catch (err) {
      setError(err.message || 'Failed to load thread')
    } finally {
      setLoading(false)
    }
  }, [threadId])

  useEffect(() => {
    load()
  }, [load])

  return { thread, loading, error, refresh: load }
}

export function useClassification(filters = {}) {
  const [results, setResults] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [resultData, statsData] = await Promise.all([
        fetchClassificationResults(filters),
        fetchClassificationStats(),
      ])
      setResults(resultData)
      setStats(statsData)
    } catch (err) {
      setError(err.message || 'Failed to load classification data')
    } finally {
      setLoading(false)
    }
  }, [filters.category, filters.email_type, filters.urgency])

  useEffect(() => {
    load()
  }, [load])

  return { results, stats, loading, error, refresh: load }
}

export function useEmailSearch() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const search = useCallback(async (query, filters = {}) => {
    if (!query) return
    setLoading(true)
    setError(null)
    try {
      const data = await searchEmails(query, filters)
      setResults(data)
    } catch (err) {
      setError(err.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }, [])

  return { results, loading, error, search }
}
