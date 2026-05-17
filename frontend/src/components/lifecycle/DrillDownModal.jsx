import { motion, AnimatePresence } from 'framer-motion'

export default function DrillDownModal({ open, title, children, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="glass max-h-[80vh] w-full max-w-3xl overflow-y-auto rounded-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{title}</h2>
              <button onClick={onClose} className="text-white/60 transition hover:text-white">
                ✕
              </button>
            </div>

            {/* Content */}
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/* ── Pre-built drill-down content renderers ─────────────────────────────── */

export function NegotiationDrillDown({ data }) {
  if (!data) return null
  const { avg_rounds, top_contracts_by_rounds = [], most_negotiated_clauses = [], correlation_rounds_cycle_time } = data

  return (
    <div className="space-y-5">
      {/* Summary KPIs */}
      <div className="flex gap-6">
        <Stat label="Average Rounds" value={avg_rounds?.toFixed(1)} />
        <Stat label="Rounds ↔ Cycle Correlation" value={correlation_rounds_cycle_time?.toFixed(2)} />
        <Stat label="Contracts Analyzed" value={top_contracts_by_rounds.length} />
      </div>

      {/* Contracts table */}
      {top_contracts_by_rounds.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-white/60">All Contracts by Negotiation Rounds</p>
          <div className="max-h-48 overflow-y-auto rounded-lg bg-white/5">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/10 text-left text-white/50">
                  <th className="px-3 py-2">Contract</th>
                  <th className="px-3 py-2">Rounds</th>
                  <th className="px-3 py-2">Cycle Days</th>
                </tr>
              </thead>
              <tbody>
                {top_contracts_by_rounds.map((c, i) => (
                  <tr key={i} className="border-b border-white/5 text-white/70">
                    <td className="px-3 py-1.5">{c.name || c.contract_id || `#${i + 1}`}</td>
                    <td className="px-3 py-1.5">{c.rounds}</td>
                    <td className="px-3 py-1.5">{c.cycle_days?.toFixed(1) ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Clauses table */}
      {most_negotiated_clauses.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-white/60">Most Negotiated Clauses</p>
          <div className="max-h-48 overflow-y-auto rounded-lg bg-white/5">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/10 text-left text-white/50">
                  <th className="px-3 py-2">Clause</th>
                  <th className="px-3 py-2">Frequency</th>
                </tr>
              </thead>
              <tbody>
                {most_negotiated_clauses.map((c, i) => (
                  <tr key={i} className="border-b border-white/5 text-white/70">
                    <td className="px-3 py-1.5">{c.clause || c.name || `Clause ${i + 1}`}</td>
                    <td className="px-3 py-1.5">{c.frequency || c.count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export function ClauseFrictionDrillDown({ data }) {
  const clauses = Array.isArray(data) ? data : []
  if (!clauses.length) return <p className="text-sm text-white/40">No clause data</p>

  return (
    <div className="max-h-[50vh] overflow-y-auto rounded-lg bg-white/5">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10 text-left text-white/50">
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Clause</th>
            <th className="px-3 py-2">Frequency</th>
          </tr>
        </thead>
        <tbody>
          {clauses.map((c, i) => (
            <tr key={i} className="border-b border-white/5 text-white/70">
              <td className="px-3 py-1.5 text-white/40">{i + 1}</td>
              <td className="px-3 py-1.5">{c.clause || c.name || `Clause ${i + 1}`}</td>
              <td className="px-3 py-1.5">{c.frequency || c.count || 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DepartmentDrillDown({ data }) {
  const items = Array.isArray(data) ? data : []
  if (!items.length) return <p className="text-sm text-white/40">No department data</p>

  return (
    <div className="max-h-[50vh] overflow-y-auto rounded-lg bg-white/5">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10 text-left text-white/50">
            <th className="px-3 py-2">Rank</th>
            <th className="px-3 py-2">Department</th>
            <th className="px-3 py-2">Members</th>
            <th className="px-3 py-2">Throughput</th>
            <th className="px-3 py-2">Avg Resp. (h)</th>
            <th className="px-3 py-2">Bottlenecks</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d, i) => (
            <tr key={i} className="border-b border-white/5 text-white/70">
              <td className="px-3 py-1.5 text-white/40">#{d.efficiency_rank}</td>
              <td className="px-3 py-1.5 font-medium">{d.department}</td>
              <td className="px-3 py-1.5">{d.member_count}</td>
              <td className="px-3 py-1.5">{d.contract_throughput}</td>
              <td className="px-3 py-1.5">{d.avg_response_time_hours?.toFixed(1)}</td>
              <td className="px-3 py-1.5">{d.bottleneck_frequency}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-2xl font-bold text-electric">{value ?? '—'}</p>
      <p className="text-[10px] text-white/50">{label}</p>
    </div>
  )
}
