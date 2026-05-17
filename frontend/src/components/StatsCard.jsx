import { motion } from 'framer-motion'

export default function StatsCard({ label, value, accent = 'border-cyan-400', icon = '📨', subtext }) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`glass rounded-xl border-l-4 ${accent} p-4`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <p className="text-xs uppercase tracking-wide text-white/70">{label}</p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="text-2xl font-semibold">{value}</p>
        <span className="text-2xl" aria-hidden>
          {icon}
        </span>
      </div>
      {subtext ? <p className="mt-1 text-xs text-white/60">{subtext}</p> : null}
    </motion.div>
  )
}
