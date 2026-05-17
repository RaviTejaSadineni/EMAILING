import { motion } from 'framer-motion'

const COLORS = ['#3b82f6', '#8b5cf6', '#a855f7', '#d946ef', '#f43f5e', '#f59e0b', '#10b981']

export default function CycleTimeChart({ distribution }) {
  if (!distribution?.bins?.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Cycle Time Distribution</p>
        <p className="mt-4 text-sm text-white/40">No cycle time data available</p>
      </div>
    )
  }

  const { bins, avg_days, median_days } = distribution
  const maxCount = Math.max(...bins.map((b) => b.count), 1)

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Cycle Time Distribution</p>
        <div className="flex gap-4">
          <span className="text-xs text-white/50">
            Avg: <span className="font-medium text-electric">{avg_days?.toFixed(1)}d</span>
          </span>
          <span className="text-xs text-white/50">
            Median: <span className="font-medium text-purple">{median_days?.toFixed(1)}d</span>
          </span>
        </div>
      </div>
      <div className="flex items-end gap-2" style={{ height: 120 }}>
        {bins.map((bin, i) => (
          <motion.div
            key={bin.label}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ duration: 0.4, delay: i * 0.06 }}
            className="group relative flex-1 origin-bottom"
          >
            <div
              className="mx-auto w-full rounded-t-md transition-opacity duration-200 group-hover:opacity-100"
              style={{
                height: `${(bin.count / maxCount) * 100}%`,
                background: `linear-gradient(to top, ${COLORS[i % COLORS.length]}66, ${COLORS[i % COLORS.length]})`,
                minHeight: 4,
                opacity: 0.75,
              }}
            />
            <div className="absolute -top-6 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-0.5 text-xs text-white group-hover:block">
              {bin.count} contracts
            </div>
          </motion.div>
        ))}
      </div>
      <div className="mt-1 flex gap-2">
        {bins.map((bin, i) => (
          <p key={i} className="flex-1 text-center text-[9px] text-white/40">
            {bin.label}
          </p>
        ))}
      </div>
    </div>
  )
}
