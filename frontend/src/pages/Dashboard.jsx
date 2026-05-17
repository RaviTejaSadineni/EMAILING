import { Suspense, lazy } from 'react'
import ActivityFeed from '../components/dashboard/ActivityFeed'
import BottleneckList from '../components/dashboard/BottleneckList'
import DonutChart from '../components/dashboard/DonutChart'
import KPICard from '../components/dashboard/KPICard'
import Loading from '../components/ui/Loading'
import { useDashboardData } from '../hooks/useDashboardData'

const DashboardScene = lazy(() => import('../components/three/DashboardScene'))

const KPI_CONFIG = [
  { key: 'total_contracts', title: 'Total Contracts', icon: '📄', accent: 'info' },
  { key: 'active_contracts', title: 'Active Contracts', icon: '🔄', accent: 'purple' },
  { key: 'avg_cycle_time_days', title: 'Avg Cycle Time', icon: '⏱️', accent: 'warning', format: (v) => `${v?.toFixed(1) || 0}d` },
  { key: 'sla_breach_rate', title: 'SLA Breach Rate', icon: '⚠️', accent: 'danger', format: (v) => `${(v * 100)?.toFixed(1) || 0}%` },
  { key: 'active_negotiations', title: 'Active Negotiations', icon: '🤝', accent: 'purple' },
  { key: 'total_emails', title: 'Total Emails', icon: '📧', accent: 'info' },
  { key: 'total_stakeholders', title: 'Stakeholders', icon: '👥', accent: 'success' },
  { key: 'avg_risk_score', title: 'Avg Risk Score', icon: '🎯', accent: 'danger', format: (v) => v?.toFixed(1) || '0' },
]

export default function Dashboard() {
  const { kpis, stageDistribution, typeDistribution, recentActivity, topBottlenecks, loading, error, refresh } =
    useDashboardData()

  return (
    <div className="relative space-y-6">
      {/* 3D Background */}
      <Suspense fallback={null}>
        <DashboardScene />
      </Suspense>

      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Analytics Dashboard</h2>
        <button
          onClick={refresh}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
        >
          ↻ Refresh
        </button>
      </div>

      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      {/* KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPI_CONFIG.map((cfg, i) => (
          <KPICard
            key={cfg.key}
            title={cfg.title}
            value={cfg.format ? cfg.format(kpis?.[cfg.key]) : kpis?.[cfg.key] ?? '—'}
            icon={cfg.icon}
            accent={cfg.accent}
            delay={i}
          />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <DonutChart data={stageDistribution?.items || []} title="Contracts by Stage" />
        <DonutChart data={typeDistribution?.items || []} title="Contract Types" />
      </div>

      {/* Activity + Bottlenecks */}
      <div className="grid gap-4 lg:grid-cols-2">
        <ActivityFeed items={recentActivity} />
        <BottleneckList items={topBottlenecks} />
      </div>
    </div>
  )
}
