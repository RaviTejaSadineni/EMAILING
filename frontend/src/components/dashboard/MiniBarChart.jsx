import { motion } from 'framer-motion'

export default function MiniBarChart({ data = [], label = '', height = 80, color = '#667eea' }) {
  if (!data.length) return null
  const maxVal = Math.max(...data.map((d) => d.value), 1)

  return (
    <div className="glass card-3d rounded-2xl p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">{label}</p>
      <div className="flex items-end gap-1" style={{ height }}>
        {data.map((item, i) => (
          <motion.div
            key={item.label || i}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ duration: 0.4, delay: i * 0.03 }}
            className="group relative flex-1 origin-bottom"
          >
            <div
              className="w-full rounded-t transition-all duration-200 group-hover:opacity-100"
              style={{
                height: `${(item.value / maxVal) * 100}%`,
                background: `linear-gradient(to top, ${color}88, ${color})`,
                minHeight: 4,
                opacity: 0.8,
              }}
            />
            <div className="absolute -top-7 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-0.5 text-xs text-white group-hover:block">
              {item.value}
            </div>
          </motion.div>
        ))}
      </div>
      {data.length <= 12 && (
        <div className="mt-1 flex gap-1">
          {data.map((item, i) => (
            <p key={i} className="flex-1 truncate text-center text-[9px] text-white/40">
              {item.label}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
