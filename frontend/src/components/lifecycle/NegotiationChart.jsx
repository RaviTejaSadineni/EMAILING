import { motion } from 'framer-motion'

const BAR_COLOR = '#8b5cf6'
const ACCENT = '#a855f7'

export default function NegotiationChart({ data, onDrillDown }) {
  if (!data) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Negotiation Analysis</p>
        <p className="mt-4 text-sm text-white/40">No negotiation data available</p>
      </div>
    )
  }

  const { avg_rounds, top_contracts_by_rounds = [], correlation_rounds_cycle_time } = data
  const maxRounds = Math.max(...top_contracts_by_rounds.map((c) => c.rounds || 0), 1)

  return (
    <div
      className="glass card-3d cursor-pointer rounded-2xl p-5 transition hover:ring-1 hover:ring-white/20"
      onClick={() => onDrillDown?.('negotiation', data)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onDrillDown?.('negotiation', data)}
    >
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Negotiation Analysis</p>
        <span className="text-[10px] text-white/40">click to drill-down</span>
      </div>

      {/* KPI row */}
      <div className="mb-4 flex gap-6">
        <div>
          <p className="text-2xl font-bold text-purple">{avg_rounds?.toFixed(1) ?? '—'}</p>
          <p className="text-[10px] text-white/50">Avg Rounds</p>
        </div>
        {correlation_rounds_cycle_time != null && (
          <div>
            <p className="text-2xl font-bold text-electric">{correlation_rounds_cycle_time.toFixed(2)}</p>
            <p className="text-[10px] text-white/50">Rounds ↔ Cycle Correlation</p>
          </div>
        )}
      </div>

      {/* Top contracts horizontal bars */}
      {top_contracts_by_rounds.length > 0 && (
        <>
          <p className="mb-2 text-[10px] font-medium uppercase text-white/50">Top Contracts by Rounds</p>
          <div className="space-y-2">
            {top_contracts_by_rounds.slice(0, 5).map((c, i) => {
              const pct = ((c.rounds || 0) / maxRounds) * 100
              return (
                <div key={i} className="flex items-center gap-2">
                  <span className="w-28 truncate text-xs text-white/60">{c.name || c.contract_id || `#${i + 1}`}</span>
                  <div className="relative h-4 flex-1 overflow-hidden rounded-full bg-white/10">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.5, delay: i * 0.08 }}
                      className="h-full rounded-full"
                      style={{ background: `linear-gradient(to right, ${BAR_COLOR}, ${ACCENT})` }}
                    />
                  </div>
                  <span className="w-8 text-right text-xs font-medium text-white/80">{c.rounds}</span>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
