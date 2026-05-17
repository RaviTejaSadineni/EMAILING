export default function ContractStats({ stats }) {
  if (!stats) return null

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="glass rounded-xl p-4 text-center">
        <p className="text-2xl font-bold text-electric">{stats.total_contracts}</p>
        <p className="text-xs text-white/50">Total Contracts</p>
      </div>
      <div className="glass rounded-xl p-4 text-center">
        <p className="text-2xl font-bold text-purple-400">
          {Object.keys(stats.by_type || {}).length}
        </p>
        <p className="text-xs text-white/50">Agreement Types</p>
      </div>
      <div className="glass rounded-xl p-4 text-center">
        <p className="text-2xl font-bold text-red-400">{stats.sla_breaches}</p>
        <p className="text-xs text-white/50">SLA Breaches</p>
      </div>
    </div>
  )
}
