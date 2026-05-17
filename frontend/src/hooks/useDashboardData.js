import { useCallback, useEffect, useState } from 'react'
import {
  fetchBottleneckAnalysis,
  fetchCycleTimeDistribution,
  fetchDashboardKPIs,
  fetchDistribution,
  fetchRecentActivity,
  fetchStageHealth,
  fetchStageTransitions,
  fetchTopBottlenecks,
  fetchVelocityTrend,
} from '../api/dashboard'

export function useDashboardData() {
  const [kpis, setKpis] = useState(null)
  const [stageDistribution, setStageDistribution] = useState(null)
  const [typeDistribution, setTypeDistribution] = useState(null)
  const [recentActivity, setRecentActivity] = useState([])
  const [topBottlenecks, setTopBottlenecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [kpiData, stages, types, activity, bottlenecks] = await Promise.all([
        fetchDashboardKPIs(),
        fetchDistribution('stages'),
        fetchDistribution('contract-types'),
        fetchRecentActivity(10),
        fetchTopBottlenecks(5),
      ])
      setKpis(kpiData)
      setStageDistribution(stages)
      setTypeDistribution(types)
      setRecentActivity(activity)
      setTopBottlenecks(bottlenecks)
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { kpis, stageDistribution, typeDistribution, recentActivity, topBottlenecks, loading, error, refresh: load }
}

export function useContractAnalytics() {
  const [stageTransitions, setStageTransitions] = useState([])
  const [stageHealth, setStageHealth] = useState(null)
  const [velocityTrend, setVelocityTrend] = useState(null)
  const [cycleTimeDistribution, setCycleTimeDistribution] = useState(null)
  const [bottlenecks, setBottlenecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [transitions, health, velocity, cycleTimes, bottleneckData] = await Promise.all([
        fetchStageTransitions(),
        fetchStageHealth(),
        fetchVelocityTrend(),
        fetchCycleTimeDistribution(),
        fetchBottleneckAnalysis(),
      ])
      setStageTransitions(transitions)
      setStageHealth(health)
      setVelocityTrend(velocity)
      setCycleTimeDistribution(cycleTimes)
      setBottlenecks(bottleneckData)
    } catch (err) {
      setError(err.message || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { stageTransitions, stageHealth, velocityTrend, cycleTimeDistribution, bottlenecks, loading, error, refresh: load }
}
