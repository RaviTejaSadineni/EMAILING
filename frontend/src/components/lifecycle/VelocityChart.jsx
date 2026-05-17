import { motion } from 'framer-motion'

export default function VelocityChart({ velocityTrend }) {
  if (!velocityTrend?.points?.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Contract Velocity</p>
        <p className="mt-4 text-sm text-white/40">No velocity data available</p>
      </div>
    )
  }

  const { points } = velocityTrend
  const maxVal = Math.max(...points.map((p) => Math.max(p.completed_count, p.started_count)), 1)
  const chartHeight = 100

  // Build SVG line paths
  const buildPath = (key) => {
    return points
      .map((p, i) => {
        const x = (i / Math.max(points.length - 1, 1)) * 100
        const y = 100 - (p[key] / maxVal) * 100
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
  }

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Contract Velocity</p>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded-sm bg-emerald-500" /> Completed
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded-sm bg-blue-500" /> Started
          </span>
        </div>
      </div>
      <div className="overflow-hidden">
        <svg viewBox={`-5 -5 110 ${chartHeight + 10}`} className="h-28 w-full" preserveAspectRatio="none">
          <motion.path
            d={buildPath('completed_count')}
            fill="none"
            stroke="#10b981"
            strokeWidth={2}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1 }}
          />
          <motion.path
            d={buildPath('started_count')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={2}
            strokeDasharray="4 2"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, delay: 0.2 }}
          />
          {/* Data points */}
          {points.map((p, i) => {
            const x = (i / Math.max(points.length - 1, 1)) * 100
            return (
              <g key={i}>
                <circle cx={x} cy={100 - (p.completed_count / maxVal) * 100} r={2.5} fill="#10b981" />
                <circle cx={x} cy={100 - (p.started_count / maxVal) * 100} r={2.5} fill="#3b82f6" />
              </g>
            )
          })}
        </svg>
      </div>
      <div className="mt-1 flex justify-between">
        {points.length <= 12 &&
          points.map((p, i) => (
            <span key={i} className="text-[9px] text-white/40">
              {p.period}
            </span>
          ))}
      </div>
    </div>
  )
}
