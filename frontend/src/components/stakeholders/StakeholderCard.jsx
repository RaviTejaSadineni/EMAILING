import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

export default function StakeholderCard({ stakeholder, index = 0, selected, onSelect }) {
  const navigate = useNavigate()
  const s = stakeholder

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={() => navigate(`/stakeholders/${s.id}`)}
      className={`glass card-3d cursor-pointer rounded-xl p-4 ${selected ? 'ring-2 ring-electric' : ''}`}
    >
      <div className="mb-3 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-white">{s.name || s.email_address}</h3>
          <p className="truncate text-xs text-white/50">{s.email_address}</p>
        </div>
        {onSelect && (
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => { e.stopPropagation(); onSelect(s.id) }}
            onClick={(e) => e.stopPropagation()}
            className="ml-2 mt-1 h-4 w-4 rounded accent-electric"
          />
        )}
      </div>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {s.department && (
          <span className="rounded-full bg-electric/20 px-2 py-0.5 text-[10px] text-electric">{s.department}</span>
        )}
        {s.role && (
          <span className="rounded-full bg-purple/20 px-2 py-0.5 text-[10px] text-purple-300">{s.role}</span>
        )}
        <span className={`rounded-full px-2 py-0.5 text-[10px] ${s.is_internal ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {s.is_internal ? 'Internal' : 'External'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-white/5 p-1.5">
          <p className="text-xs font-bold text-electric">{s.total_emails}</p>
          <p className="text-[10px] text-white/40">Emails</p>
        </div>
        <div className="rounded-lg bg-white/5 p-1.5">
          <p className="text-xs font-bold text-purple-400">{s.total_contracts}</p>
          <p className="text-[10px] text-white/40">Contracts</p>
        </div>
        <div className="rounded-lg bg-white/5 p-1.5">
          <p className="text-xs font-bold text-green-400">{s.avg_response_time ? `${s.avg_response_time.toFixed(1)}h` : '—'}</p>
          <p className="text-[10px] text-white/40">Resp Time</p>
        </div>
      </div>
    </motion.div>
  )
}
