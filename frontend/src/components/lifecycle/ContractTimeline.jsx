import { motion } from 'framer-motion'

export default function ContractTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Contract Timeline</p>
        <p className="mt-4 text-sm text-white/40">No timeline events available</p>
      </div>
    )
  }

  const typeColors = {
    stage_enter: 'bg-blue-500',
    stage_exit: 'bg-purple-500',
    email: 'bg-cyan-500',
    created: 'bg-emerald-500',
    sla_warning: 'bg-amber-500',
    sla_breach: 'bg-red-500',
  }

  const typeIcons = {
    stage_enter: '📥',
    stage_exit: '📤',
    email: '📧',
    created: '🆕',
    sla_warning: '⚠️',
    sla_breach: '🚨',
  }

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Contract Timeline</p>
      <div className="relative ml-4 border-l border-white/20 pl-6">
        {events.map((event, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="relative mb-4 last:mb-0"
          >
            {/* Dot on timeline */}
            <div
              className={`absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-navy ${typeColors[event.event_type] || 'bg-white/40'}`}
            />
            <div className="rounded-lg bg-white/5 p-3">
              <div className="flex items-center gap-2">
                <span className="text-sm">{typeIcons[event.event_type] || '📋'}</span>
                <span className="text-xs font-medium text-white/80">{event.description}</span>
              </div>
              <div className="mt-1 flex items-center gap-3">
                {event.stage && (
                  <span className="rounded-full bg-electric/20 px-2 py-0.5 text-[10px] text-electric">{event.stage}</span>
                )}
                {event.actor && <span className="text-[10px] text-white/40">by {event.actor}</span>}
                {event.date && (
                  <span className="text-[10px] text-white/30">{new Date(event.date).toLocaleString()}</span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
