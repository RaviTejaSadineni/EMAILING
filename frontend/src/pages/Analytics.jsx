import { useCallback, useState } from 'react'
import AnalyticsToolbar from '../components/lifecycle/AnalyticsToolbar'
import ClauseFrictionChart from '../components/lifecycle/ClauseFrictionChart'
import CycleTimeChart from '../components/lifecycle/CycleTimeChart'
import DepartmentAnalyticsChart from '../components/lifecycle/DepartmentAnalyticsChart'
import DrillDownModal, {
  ClauseFrictionDrillDown,
  DepartmentDrillDown,
  NegotiationDrillDown,
} from '../components/lifecycle/DrillDownModal'
import NegotiationChart from '../components/lifecycle/NegotiationChart'
import SankeyFlow from '../components/lifecycle/SankeyFlow'
import StageHealthGrid from '../components/lifecycle/StageHealthGrid'
import StagePipeline from '../components/lifecycle/StagePipeline'
import VelocityChart from '../components/lifecycle/VelocityChart'
import Loading from '../components/ui/Loading'
import { useAdvancedAnalytics, useAnalyticsFilters } from '../hooks/useAdvancedAnalytics'
import { useContractAnalytics, useDashboardData } from '../hooks/useDashboardData'
import exportCsv from '../utils/exportCsv'

const DRILL_TITLES = {
  negotiation: 'Negotiation Analysis — Detail',
  clause_friction: 'Clause Friction — Detail',
  departments: 'Department Analytics — Detail',
}

export default function Analytics() {
  const { stageDistribution, loading: dashLoading } = useDashboardData()
  const { stageTransitions, stageHealth, velocityTrend, cycleTimeDistribution, loading, error, refresh } =
    useContractAnalytics()
  const {
    negotiation,
    departments,
    loading: advLoading,
    error: advError,
    refresh: advRefresh,
  } = useAdvancedAnalytics()

  const {
    filters,
    updateFilter,
    resetFilters,
    savedPresets,
    applyPreset,
    saveCurrentAsPreset,
    deletePreset,
  } = useAnalyticsFilters()

  // ── Drill-down state ──
  const [drillDown, setDrillDown] = useState({ open: false, type: null, data: null })

  const openDrillDown = useCallback((type, data) => {
    setDrillDown({ open: true, type, data })
  }, [])

  const closeDrillDown = useCallback(() => {
    setDrillDown({ open: false, type: null, data: null })
  }, [])

  // ── Export handler ──
  const handleExport = useCallback(() => {
    const rows = []

    // Stage health data
    if (stageHealth?.items) {
      stageHealth.items.forEach((item) =>
        rows.push({
          section: 'Stage Health',
          stage: item.stage,
          contract_count: item.contract_count,
          on_track: item.white_count,
          at_risk: item.yellow_count,
          critical: item.red_count,
          avg_days: item.avg_days_in_stage?.toFixed(1),
        }),
      )
    }

    // Department data
    if (departments?.items) {
      departments.items.forEach((d) =>
        rows.push({
          section: 'Department',
          department: d.department,
          members: d.member_count,
          throughput: d.contract_throughput,
          avg_response_hours: d.avg_response_time_hours?.toFixed(1),
          bottlenecks: d.bottleneck_frequency,
          efficiency_rank: d.efficiency_rank,
        }),
      )
    }

    // Negotiation data
    if (negotiation?.top_contracts_by_rounds) {
      negotiation.top_contracts_by_rounds.forEach((c) =>
        rows.push({
          section: 'Negotiation',
          contract: c.name || c.contract_id,
          rounds: c.rounds,
          cycle_days: c.cycle_days?.toFixed(1) ?? '',
        }),
      )
    }

    if (!rows.length) return
    exportCsv('analytics-export.csv', rows)
  }, [stageHealth, departments, negotiation])

  // ── Combined refresh ──
  const refreshAll = useCallback(() => {
    refresh()
    advRefresh()
  }, [refresh, advRefresh])

  const isLoading = loading || dashLoading || advLoading
  const combinedError = error || advError

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Contract Lifecycle Analytics</h2>
        <button
          onClick={refreshAll}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Toolbar: search, filters, saved presets, export */}
      <AnalyticsToolbar
        filters={filters}
        onFilterChange={updateFilter}
        onReset={resetFilters}
        savedPresets={savedPresets}
        onApplyPreset={applyPreset}
        onSavePreset={(name) => saveCurrentAsPreset(name)}
        onDeletePreset={deletePreset}
        onExport={handleExport}
      />

      {isLoading && <Loading />}
      {combinedError && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{combinedError}</p>}

      {/* Stage Pipeline */}
      <StagePipeline stageDistribution={stageDistribution} />

      {/* Sankey Flow */}
      <SankeyFlow transitions={stageTransitions} />

      {/* Charts Row — Original */}
      <div className="grid gap-4 lg:grid-cols-2">
        <CycleTimeChart distribution={cycleTimeDistribution} />
        <VelocityChart velocityTrend={velocityTrend} />
      </div>

      {/* Advanced Charts Row — Step 19 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <NegotiationChart data={negotiation} onDrillDown={openDrillDown} />
        <ClauseFrictionChart data={negotiation} onDrillDown={openDrillDown} />
      </div>

      {/* Department Analytics — Step 19 */}
      <DepartmentAnalyticsChart data={departments} onDrillDown={openDrillDown} />

      {/* Stage Health */}
      <StageHealthGrid stageHealth={stageHealth} />

      {/* Drill-down Modal — Step 20 */}
      <DrillDownModal
        open={drillDown.open}
        title={DRILL_TITLES[drillDown.type] || 'Detail'}
        onClose={closeDrillDown}
      >
        {drillDown.type === 'negotiation' && <NegotiationDrillDown data={drillDown.data} />}
        {drillDown.type === 'clause_friction' && <ClauseFrictionDrillDown data={drillDown.data} />}
        {drillDown.type === 'departments' && <DepartmentDrillDown data={drillDown.data} />}
      </DrillDownModal>
    </div>
  )
}
