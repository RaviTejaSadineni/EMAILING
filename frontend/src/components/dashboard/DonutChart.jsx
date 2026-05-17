import { motion } from 'framer-motion'

const COLORS = ['#667eea', '#764ba2', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899']

export default function DonutChart({ data = [], title = '', size = 160 }) {
  if (!data.length) return null
  const total = data.reduce((s, d) => s + d.count, 0)
  if (total === 0) return null

  const radius = size / 2 - 12
  const circumference = 2 * Math.PI * radius

  let accumulated = 0
  const segments = data.map((item, i) => {
    const pct = item.count / total
    const offset = accumulated
    accumulated += pct
    return { ...item, pct, offset, color: COLORS[i % COLORS.length] }
  })

  return (
    <div className="glass card-3d rounded-2xl p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
      <div className="flex items-center gap-4">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
          {segments.map((seg, i) => (
            <motion.circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={20}
              strokeDasharray={`${seg.pct * circumference} ${circumference}`}
              strokeDashoffset={-seg.offset * circumference}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="origin-center -rotate-90"
              style={{ transformOrigin: `${size / 2}px ${size / 2}px` }}
            />
          ))}
          <text x={size / 2} y={size / 2 - 6} textAnchor="middle" className="fill-white text-2xl font-bold">
            {total}
          </text>
          <text x={size / 2} y={size / 2 + 12} textAnchor="middle" className="fill-white/50 text-[10px]">
            Total
          </text>
        </svg>
        <div className="flex flex-col gap-1.5 overflow-hidden">
          {segments.slice(0, 6).map((seg, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: seg.color }} />
              <span className="truncate text-white/70">{seg.label}</span>
              <span className="ml-auto font-medium text-white/90">{seg.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
