import { motion } from 'framer-motion'

const METRICS = [
  { key: 'avg_response_time_hours', label: 'Avg Response Time', format: (v) => `${v?.toFixed(1) || 0}h`, best: 'min' },
  { key: 'email_volume', label: 'Email Volume', format: (v) => v || 0, best: 'max' },
  { key: 'contract_count', label: 'Contracts', format: (v) => v || 0, best: 'max' },
  { key: 'sla_breach_rate', label: 'SLA Breach Rate', format: (v) => `${((v || 0) * 100).toFixed(1)}%`, best: 'min' },
  { key: 'bottleneck_frequency', label: 'Bottlenecks', format: (v) => v || 0, best: 'min' },
]

export default function ComparisonTable({ comparison }) {
  if (!comparison?.items?.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Stakeholder Comparison</p>
        <p className="mt-4 text-sm text-white/40">Select at least 2 stakeholders to compare</p>
      </div>
    )
  }

  const { items } = comparison

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass card-3d overflow-x-auto rounded-2xl p-5"
    >
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Stakeholder Comparison</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10">
            <th className="pb-2 text-left text-xs text-white/40">Metric</th>
            {items.map((item) => (
              <th key={item.stakeholder_id} className="pb-2 text-center text-xs text-white/70">
                {item.name || item.stakeholder_id?.slice(0, 8)}
                {item.department && <span className="block text-[10px] text-white/40">{item.department}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRICS.map((metric) => {
            const values = items.map((item) => item[metric.key] || 0)
            const best = metric.best === 'min' ? Math.min(...values) : Math.max(...values)
            return (
              <tr key={metric.key} className="border-b border-white/5">
                <td className="py-2 text-xs text-white/60">{metric.label}</td>
                {items.map((item, i) => {
                  const val = item[metric.key] || 0
                  const isBest = val === best
                  return (
                    <td key={item.stakeholder_id} className={`py-2 text-center text-xs ${isBest ? 'font-bold text-green-400' : 'text-white/70'}`}>
                      {metric.format(val)}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </motion.div>
  )
}
