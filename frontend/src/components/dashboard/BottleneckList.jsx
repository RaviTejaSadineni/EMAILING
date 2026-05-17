import { motion } from 'framer-motion'

export default function BottleneckList({ items = [] }) {
  if (!items.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Top Bottlenecks</p>
        <p className="mt-4 text-sm text-white/40">No bottleneck contracts found</p>
      </div>
    )
  }

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Top Bottlenecks</p>
      <div className="space-y-2">
        {items.map((item, i) => (
          <motion.div
            key={item.contract_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center justify-between rounded-lg bg-white/5 p-3"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white/90">{item.agreement_name || 'Unnamed Contract'}</p>
              <p className="text-xs text-white/50">{item.current_stage || 'Unknown Stage'}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-red-400">{item.days_stalled?.toFixed(0)}d</p>
              <p className="text-[10px] text-white/40">stalled</p>
            </div>
            {item.sla_breached && (
              <span className="ml-2 rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] font-medium text-red-400">SLA</span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
