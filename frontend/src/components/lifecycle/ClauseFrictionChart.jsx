import { motion } from 'framer-motion'

const COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#3b82f6', '#10b981', '#d946ef', '#a855f7']

export default function ClauseFrictionChart({ data, onDrillDown }) {
  const clauses = data?.most_negotiated_clauses || []

  if (!clauses.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Clause Friction</p>
        <p className="mt-4 text-sm text-white/40">No clause friction data available</p>
      </div>
    )
  }

  const maxFreq = Math.max(...clauses.map((c) => c.frequency || c.count || 0), 1)

  return (
    <div
      className="glass card-3d cursor-pointer rounded-2xl p-5 transition hover:ring-1 hover:ring-white/20"
      onClick={() => onDrillDown?.('clause_friction', clauses)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onDrillDown?.('clause_friction', clauses)}
    >
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Clause Friction</p>
        <span className="text-[10px] text-white/40">click to drill-down</span>
      </div>

      <div className="space-y-2">
        {clauses.slice(0, 8).map((clause, i) => {
          const freq = clause.frequency || clause.count || 0
          const pct = (freq / maxFreq) * 100
          const color = COLORS[i % COLORS.length]
          const label = clause.clause || clause.name || `Clause ${i + 1}`

          return (
            <div key={i} className="flex items-center gap-2">
              <span className="w-32 truncate text-xs text-white/60" title={label}>
                {label}
              </span>
              <div className="relative h-3.5 flex-1 overflow-hidden rounded-full bg-white/10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.5, delay: i * 0.06 }}
                  className="h-full rounded-full"
                  style={{ background: `linear-gradient(to right, ${color}99, ${color})` }}
                />
              </div>
              <span className="w-8 text-right text-xs font-medium text-white/80">{freq}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
