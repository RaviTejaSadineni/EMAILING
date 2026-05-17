import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import NetworkGraph from '../components/stakeholders/NetworkGraph'
import HeatmapChart from '../components/stakeholders/HeatmapChart'
import Loading from '../components/ui/Loading'
import { useStakeholderDetail } from '../hooks/useStakeholderData'

export default function StakeholderProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { detail, contracts, emails, analytics, performance, network, loading, error } = useStakeholderDetail(id)

  if (loading) return <Loading />
  if (error) return <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>
  if (!detail) return <p className="text-sm text-white/40">Stakeholder not found.</p>

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/stakeholders')}
        className="text-sm text-white/50 transition hover:text-white"
      >
        ← Back to Stakeholders
      </button>

      {/* Profile Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass card-3d rounded-2xl p-6"
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold">{detail.name || detail.email_address}</h2>
            <p className="text-sm text-white/50">{detail.email_address}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {detail.department && (
                <span className="rounded-full bg-electric/20 px-3 py-1 text-xs text-electric">{detail.department}</span>
              )}
              {detail.role && (
                <span className="rounded-full bg-purple/20 px-3 py-1 text-xs text-purple-300">{detail.role}</span>
              )}
              <span
                className={`rounded-full px-3 py-1 text-xs ${
                  detail.is_internal ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}
              >
                {detail.is_internal ? 'Internal' : 'External'}
              </span>
            </div>
          </div>
          {detail.influence_score != null && (
            <div className="text-center">
              <p className="text-3xl font-bold text-electric">{detail.influence_score.toFixed(1)}</p>
              <p className="text-[10px] text-white/40">Influence Score</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Stats Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatBox label="Total Emails" value={detail.total_emails} icon="📧" />
        <StatBox label="Total Contracts" value={detail.total_contracts} icon="📄" />
        <StatBox
          label="Avg Response Time"
          value={detail.avg_response_time ? `${detail.avg_response_time.toFixed(1)}h` : '—'}
          icon="⏱️"
        />
        <StatBox
          label="Influence Score"
          value={detail.influence_score?.toFixed(1) || '—'}
          icon="⭐"
        />
      </div>

      {/* Performance Metrics */}
      {performance && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass card-3d rounded-2xl p-5"
        >
          <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Performance Metrics</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MiniStat label="Active Contracts" value={performance.active_contracts} />
            <MiniStat label="Completed Contracts" value={performance.completed_contracts} />
            <MiniStat label="SLA Breached" value={performance.sla_breached_contracts} accent="red" />
            <MiniStat label="SLA Breach Rate" value={`${(performance.sla_breach_rate * 100).toFixed(1)}%`} accent="red" />
            <MiniStat label="Bottleneck Count" value={performance.bottleneck_count} accent="yellow" />
            <MiniStat label="Avg Delay Caused" value={`${performance.avg_delay_caused_hours.toFixed(1)}h`} accent="yellow" />
            <MiniStat
              label="Response Time (avg)"
              value={`${performance.response_time?.avg_hours?.toFixed(1) || 0}h`}
            />
            <MiniStat
              label="Response Time Trend"
              value={performance.response_time?.trend || '—'}
              accent={performance.response_time?.trend === 'improving' ? 'green' : performance.response_time?.trend === 'worsening' ? 'red' : 'white'}
            />
          </div>
        </motion.div>
      )}

      {/* Analytics Heatmaps */}
      <div className="grid gap-4 lg:grid-cols-2">
        {analytics?.response_time_distribution && (
          <HeatmapChart data={analytics.response_time_distribution} title="Response Time Distribution" />
        )}
        {analytics?.communication_patterns && (
          <HeatmapChart data={analytics.communication_patterns} title="Communication Patterns" />
        )}
      </div>

      {/* Network Graph */}
      {network && <NetworkGraph network={network} />}

      {/* Contracts List */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass card-3d rounded-2xl p-5"
      >
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">
          Contracts ({contracts.length})
        </p>
        {contracts.length === 0 ? (
          <p className="text-sm text-white/40">No contracts found.</p>
        ) : (
          <div className="space-y-2">
            {contracts.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                <div>
                  <p className="text-sm font-medium text-white">{c.agreement_name || c.id}</p>
                  <p className="text-xs text-white/40">{c.contract_type} • {c.current_stage}</p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] ${
                    c.sla_status === 'breached'
                      ? 'bg-red-500/20 text-red-400'
                      : c.sla_status === 'at_risk'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-green-500/20 text-green-400'
                  }`}
                >
                  {c.sla_status || 'on_track'}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Recent Emails */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass card-3d rounded-2xl p-5"
      >
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">
          Recent Emails ({emails.length})
        </p>
        {emails.length === 0 ? (
          <p className="text-sm text-white/40">No emails found.</p>
        ) : (
          <div className="space-y-2">
            {emails.slice(0, 20).map((e) => (
              <div key={e.id} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                <p className="truncate text-sm text-white/80">{e.subject || '(no subject)'}</p>
                <span className="shrink-0 text-[10px] text-white/30">
                  {e.date ? new Date(e.date).toLocaleDateString() : '—'}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}

function StatBox({ label, value, icon }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass card-3d rounded-xl p-4 text-center"
    >
      <span className="text-2xl" aria-hidden>{icon}</span>
      <p className="mt-1 text-xl font-bold text-white">{value}</p>
      <p className="text-[10px] text-white/40">{label}</p>
    </motion.div>
  )
}

function MiniStat({ label, value, accent = 'white' }) {
  const colorMap = {
    white: 'text-white',
    red: 'text-red-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
  }
  return (
    <div className="rounded-lg bg-white/5 p-3">
      <p className={`text-sm font-bold ${colorMap[accent] || 'text-white'}`}>{value}</p>
      <p className="text-[10px] text-white/40">{label}</p>
    </div>
  )
}
