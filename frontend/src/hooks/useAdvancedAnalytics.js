import { useCallback, useEffect, useState } from 'react'
import {
  createSavedFilter,
  deleteSavedFilter as apiDeleteSavedFilter,
  fetchDepartmentAnalytics,
  fetchNegotiationAnalysis,
  fetchSavedFilters,
} from '../api/dashboard'

// ── Advanced analytics data ─────────────────────────────────────────────────

export function useAdvancedAnalytics() {
  const [negotiation, setNegotiation] = useState(null)
  const [departments, setDepartments] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [neg, dept] = await Promise.all([
        fetchNegotiationAnalysis(),
        fetchDepartmentAnalytics(),
      ])
      setNegotiation(neg)
      setDepartments(dept)
    } catch (err) {
      setError(err.message || 'Failed to load advanced analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { negotiation, departments, loading, error, refresh: load }
}

// ── Filters / presets / search ──────────────────────────────────────────────

const DEFAULT_FILTERS = {
  search: '',
  dateFrom: '',
  dateTo: '',
  department: '',
  stage: '',
}

export function useAnalyticsFilters() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [savedPresets, setSavedPresets] = useState([])
  const [presetsLoading, setPresetsLoading] = useState(false)

  // ── load presets ──
  const loadPresets = useCallback(async () => {
    setPresetsLoading(true)
    try {
      const list = await fetchSavedFilters()
      setSavedPresets(list)
    } catch {
      /* ignore – saved filters are optional */
    } finally {
      setPresetsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPresets()
  }, [loadPresets])

  // ── mutators ──
  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => setFilters(DEFAULT_FILTERS), [])

  const applyPreset = useCallback((preset) => {
    if (!preset?.filter_params) return
    setFilters((prev) => ({ ...prev, ...preset.filter_params }))
  }, [])

  const saveCurrentAsPreset = useCallback(
    async (name, description) => {
      const created = await createSavedFilter({
        name,
        description: description || null,
        filter_params: filters,
        is_default: false,
      })
      setSavedPresets((prev) => [...prev, created])
      return created
    },
    [filters],
  )

  const deletePreset = useCallback(async (id) => {
    await apiDeleteSavedFilter(id)
    setSavedPresets((prev) => prev.filter((p) => p.id !== id))
  }, [])

  // ── derived helpers for data filtering ──
  const matches = useCallback(
    (item) => {
      if (filters.search) {
        const q = filters.search.toLowerCase()
        const text = JSON.stringify(item).toLowerCase()
        if (!text.includes(q)) return false
      }
      if (filters.department && item.department && item.department !== filters.department) return false
      if (filters.stage && item.stage && item.stage !== filters.stage) return false
      return true
    },
    [filters],
  )

  return {
    filters,
    updateFilter,
    resetFilters,
    savedPresets,
    presetsLoading,
    applyPreset,
    saveCurrentAsPreset,
    deletePreset,
    matches,
  }
}
