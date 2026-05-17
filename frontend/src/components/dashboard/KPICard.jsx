import { motion } from 'framer-motion'

const ACCENT_MAP = {
  success: 'from-emerald-500 to-teal-400',
  warning: 'from-amber-500 to-orange-400',
  danger: 'from-red-500 to-pink-400',
  info: 'from-blue-500 to-cyan-400',
  purple: 'from-purple-500 to-indigo-400',
  default: 'from-electric to-purple',
}

export default function KPICard({ title, value, subtitle, icon, trend, trendLabel, accent = 'default', delay = 0 }) {
  const gradient = ACCENT_MAP[accent] || ACCENT_MAP.default
  const trendUp = trend > 0
  const trendDown = trend < 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, rotateX: 8 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration: 0.5, delay: delay * 0.1, ease: 'easeOut' }}
      whileHover={{ y: -6, scale: 1.02, rotateX: -2 }}
      className="glass card-3d group relative overflow-hidden rounded-2xl p-5"
      style={{ perspective: '1000px', transformStyle: 'preserve-3d' }}
    >
      {/* Gradient accent bar */}
      <div className={`absolute left-0 top-0 h-1 w-full bg-gradient-to-r ${gradient} opacity-80`} />

      {/* Glow effect on hover */}
      <div className={`absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br ${gradient} opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-30`} />

      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-white/50">{subtitle}</p>}
          {trend !== undefined && trend !== null && (
            <div className="mt-2 flex items-center gap-1.5">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  trendUp ? 'bg-emerald-500/20 text-emerald-400' : trendDown ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/60'
                }`}
              >
                {trendUp ? '↑' : trendDown ? '↓' : '→'} {Math.abs(trend).toFixed(1)}%
              </span>
              {trendLabel && <span className="text-xs text-white/40">{trendLabel}</span>}
            </div>
          )}
        </div>
        {icon && (
          <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-xl shadow-lg`}>
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  )
}
