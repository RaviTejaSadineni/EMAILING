import { motion } from 'framer-motion'

function getHeatColor(value, max) {
  const intensity = max > 0 ? value / max : 0
  if (intensity > 0.8) return 'bg-red-500/80'
  if (intensity > 0.6) return 'bg-orange-500/70'
  if (intensity > 0.4) return 'bg-yellow-500/60'
  if (intensity > 0.2) return 'bg-green-500/50'
  return 'bg-blue-500/30'
}

export default function HeatmapChart({ data, title = 'Activity Heatmap' }) {
  if (!data || typeof data !== 'object') {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
        <p className="mt-4 text-sm text-white/40">No heatmap data available</p>
      </div>
    )
  }

  const entries = Object.entries(data).filter(([, v]) => typeof v === 'number')
  if (entries.length === 0) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
        <p className="mt-4 text-sm text-white/40">No heatmap data available</p>
      </div>
    )
  }

  const max = Math.max(...entries.map(([, v]) => v))

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass card-3d rounded-2xl p-5"
    >
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.min(entries.length, 6)}, 1fr)` }}>
        {entries.map(([label, value], i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            className={`flex flex-col items-center justify-center rounded-lg p-3 ${getHeatColor(value, max)}`}
          >
            <span className="text-lg font-bold text-white">{value}</span>
            <span className="mt-1 text-center text-[10px] leading-tight text-white/70">{label}</span>
          </motion.div>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-end gap-1 text-[10px] text-white/40">
        <span>Low</span>
        <span className="inline-block h-2 w-4 rounded bg-blue-500/30" />
        <span className="inline-block h-2 w-4 rounded bg-green-500/50" />
        <span className="inline-block h-2 w-4 rounded bg-yellow-500/60" />
        <span className="inline-block h-2 w-4 rounded bg-orange-500/70" />
        <span className="inline-block h-2 w-4 rounded bg-red-500/80" />
        <span>High</span>
      </div>
    </motion.div>
  )
}
