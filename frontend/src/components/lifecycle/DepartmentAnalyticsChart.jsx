import { motion } from 'framer-motion'

export default function DepartmentAnalyticsChart({ data, onDrillDown }) {
  const items = data?.items || []

  if (!items.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Department Analytics</p>
        <p className="mt-4 text-sm text-white/40">No department data available</p>
      </div>
    )
  }

  const maxThroughput = Math.max(...items.map((d) => d.contract_throughput || 0), 1)
  const maxResponse = Math.max(...items.map((d) => d.avg_response_time_hours || 0), 1)

  return (
    <div
      className="glass card-3d cursor-pointer rounded-2xl p-5 transition hover:ring-1 hover:ring-white/20"
      onClick={() => onDrillDown?.('departments', items)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onDrillDown?.('departments', items)}
    >
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Department Analytics</p>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded-sm bg-blue-500" /> Throughput
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded-sm bg-amber-500" /> Resp. Time
          </span>
          <span className="text-white/40">click to drill-down</span>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((dept, i) => {
          const throughputPct = ((dept.contract_throughput || 0) / maxThroughput) * 100
          const responsePct = ((dept.avg_response_time_hours || 0) / maxResponse) * 100
          return (
            <motion.div
              key={dept.department}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-lg bg-white/5 p-3"
            >
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-white/80">{dept.department}</span>
                <div className="flex gap-3 text-[10px] text-white/50">
                  <span>{dept.member_count} members</span>
                  <span>Rank #{dept.efficiency_rank}</span>
                </div>
              </div>

              {/* Throughput bar */}
              <div className="mb-1 flex items-center gap-2">
                <span className="w-16 text-[10px] text-white/40">Throughput</span>
                <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-white/10">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${throughputPct}%` }}
                    transition={{ duration: 0.5, delay: i * 0.06 }}
                    className="h-full rounded-full bg-blue-500"
                  />
                </div>
                <span className="w-10 text-right text-[10px] font-medium text-white/70">{dept.contract_throughput}</span>
              </div>

              {/* Response time bar */}
              <div className="flex items-center gap-2">
                <span className="w-16 text-[10px] text-white/40">Resp. Time</span>
                <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-white/10">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${responsePct}%` }}
                    transition={{ duration: 0.5, delay: i * 0.06 + 0.05 }}
                    className="h-full rounded-full bg-amber-500"
                  />
                </div>
                <span className="w-10 text-right text-[10px] font-medium text-white/70">
                  {dept.avg_response_time_hours?.toFixed(1)}h
                </span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
