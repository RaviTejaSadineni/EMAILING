import { motion } from 'framer-motion'

export default function ActivityFeed({ items = [] }) {
  if (!items.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Recent Activity</p>
        <p className="mt-4 text-sm text-white/40">No recent activity</p>
      </div>
    )
  }

  const typeIcons = {
    email: '📧',
    stage_transition: '🔄',
    contract_created: '📝',
    sla_breach: '⚠️',
  }

  const typeColors = {
    email: 'border-blue-500',
    stage_transition: 'border-purple-500',
    contract_created: 'border-emerald-500',
    sla_breach: 'border-red-500',
  }

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Recent Activity</p>
      <div className="space-y-3">
        {items.map((item, i) => (
          <motion.div
            key={item.entity_id + i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`flex items-start gap-3 rounded-lg border-l-2 ${typeColors[item.activity_type] || 'border-white/20'} bg-white/5 p-3`}
          >
            <span className="mt-0.5 text-base">{typeIcons[item.activity_type] || '📋'}</span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white/90">{item.title}</p>
              <p className="mt-0.5 truncate text-xs text-white/50">{item.description}</p>
              <p className="mt-1 text-[10px] text-white/30">
                {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
