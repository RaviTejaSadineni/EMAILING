import { motion } from 'framer-motion'

const HEALTH_COLORS = {
  green: '#10b981',
  yellow: '#f59e0b',
  red: '#ef4444',
}

export default function StageHealthGrid({ stageHealth }) {
  if (!stageHealth?.items?.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Stage Health</p>
        <p className="mt-4 text-sm text-white/40">No stage health data available</p>
      </div>
    )
  }

  const { items } = stageHealth

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Stage Health Overview</p>
      <div className="space-y-3">
        {items.map((item, i) => {
          const total = item.contract_count || 1
          const greenPct = (item.white_count / total) * 100
          const yellowPct = (item.yellow_count / total) * 100
          const redPct = (item.red_count / total) * 100

          return (
            <motion.div
              key={item.stage}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-lg bg-white/5 p-3"
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium text-white/80">{item.stage}</span>
                <div className="flex items-center gap-3 text-xs text-white/50">
                  <span>{item.contract_count} contracts</span>
                  <span>{item.avg_days_in_stage?.toFixed(1)}d avg</span>
                </div>
              </div>
              {/* Health bar */}
              <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-white/10">
                {greenPct > 0 && (
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${greenPct}%` }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    style={{ backgroundColor: HEALTH_COLORS.green }}
                  />
                )}
                {yellowPct > 0 && (
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${yellowPct}%` }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                    style={{ backgroundColor: HEALTH_COLORS.yellow }}
                  />
                )}
                {redPct > 0 && (
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${redPct}%` }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    style={{ backgroundColor: HEALTH_COLORS.red }}
                  />
                )}
              </div>
              <div className="mt-1 flex gap-3 text-[10px]">
                <span style={{ color: HEALTH_COLORS.green }}>✓ {item.white_count}</span>
                <span style={{ color: HEALTH_COLORS.yellow }}>⚠ {item.yellow_count}</span>
                <span style={{ color: HEALTH_COLORS.red }}>✕ {item.red_count}</span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
