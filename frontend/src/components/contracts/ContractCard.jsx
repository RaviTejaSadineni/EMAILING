import { motion } from 'framer-motion'

function riskColor(score) {
  if (score == null) return 'text-white/40'
  if (score >= 0.7) return 'text-red-400'
  if (score >= 0.4) return 'text-yellow-400'
  return 'text-green-400'
}

function stageColor(stage) {
  const colors = {
    Request: 'bg-blue-500/20 text-blue-400',
    'Legal Review': 'bg-purple-500/20 text-purple-400',
    'Finance Review': 'bg-indigo-500/20 text-indigo-400',
    'Procurement/Compliance': 'bg-cyan-500/20 text-cyan-400',
    'Redline Negotiation': 'bg-orange-500/20 text-orange-400',
    'Leadership Sign-off': 'bg-emerald-500/20 text-emerald-400',
    'Repository & Obligation Tracking': 'bg-green-500/20 text-green-400',
  }
  return colors[stage] || 'bg-white/10 text-white/60'
}

export default function ContractCard({ contract, index = 0, onClick }) {
  const c = contract

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={() => onClick?.(c.id)}
      className="glass card-3d cursor-pointer rounded-xl p-4"
    >
      <div className="mb-3">
        <h3 className="truncate text-sm font-semibold text-white">
          {c.agreement_name || 'Untitled Contract'}
        </h3>
        <p className="truncate text-xs text-white/50">
          {c.counterparty_name || c.counterparty_email || 'Unknown counterparty'}
        </p>
      </div>

      <div className="mb-3 flex flex-wrap gap-1.5">
        {c.agreement_type && (
          <span className="rounded-full bg-electric/20 px-2 py-0.5 text-[10px] text-electric">
            {c.agreement_type}
          </span>
        )}
        {c.current_stage && (
          <span className={`rounded-full px-2 py-0.5 text-[10px] ${stageColor(c.current_stage)}`}>
            {c.current_stage}
          </span>
        )}
        {c.sla_breached && (
          <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] text-red-400">
            SLA Breached
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 text-center">
        <div className="rounded-lg bg-white/5 p-1.5">
          <p className={`text-xs font-bold ${riskColor(c.risk_score)}`}>
            {c.risk_score != null ? (c.risk_score * 100).toFixed(0) + '%' : '—'}
          </p>
          <p className="text-[10px] text-white/40">Risk</p>
        </div>
        <div className="rounded-lg bg-white/5 p-1.5">
          <p className="text-xs font-bold text-purple-400">
            {c.complexity_score != null ? (c.complexity_score * 100).toFixed(0) + '%' : '—'}
          </p>
          <p className="text-[10px] text-white/40">Complexity</p>
        </div>
      </div>
    </motion.div>
  )
}
