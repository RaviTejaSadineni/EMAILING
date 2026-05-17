import CycleTimeChart from '../components/lifecycle/CycleTimeChart'
import SankeyFlow from '../components/lifecycle/SankeyFlow'
import StagePipeline from '../components/lifecycle/StagePipeline'
import StageHealthGrid from '../components/lifecycle/StageHealthGrid'
import VelocityChart from '../components/lifecycle/VelocityChart'
import Loading from '../components/ui/Loading'
import { useContractAnalytics, useDashboardData } from '../hooks/useDashboardData'

export default function Analytics() {
  const { stageDistribution, loading: dashLoading } = useDashboardData()
  const { stageTransitions, stageHealth, velocityTrend, cycleTimeDistribution, loading, error, refresh } =
    useContractAnalytics()

  const isLoading = loading || dashLoading

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Contract Lifecycle Analytics</h2>
        <button
          onClick={refresh}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
        >
          ↻ Refresh
        </button>
      </div>

      {isLoading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      {/* Stage Pipeline */}
      <StagePipeline stageDistribution={stageDistribution} />

      {/* Sankey Flow */}
      <SankeyFlow transitions={stageTransitions} />

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <CycleTimeChart distribution={cycleTimeDistribution} />
        <VelocityChart velocityTrend={velocityTrend} />
      </div>

      {/* Stage Health */}
      <StageHealthGrid stageHealth={stageHealth} />
    </div>
  )
}
