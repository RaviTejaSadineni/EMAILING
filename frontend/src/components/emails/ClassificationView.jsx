import { motion } from 'framer-motion'

const URGENCY_COLORS = {
  Critical: 'bg-red-500',
  High: 'bg-orange-500',
  Medium: 'bg-yellow-500',
  Low: 'bg-green-500',
}

const SENTIMENT_COLORS = {
  Positive: 'text-green-400',
  Neutral: 'text-white/60',
  Negative: 'text-red-400',
}

function BarChart({ data, title, color = 'bg-electric' }) {
  if (!data || Object.keys(data).length === 0) return null
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = Math.max(...entries.map(([, v]) => v))

  return (
    <div className="glass card-3d rounded-xl p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">{title}</p>
      <div className="space-y-2">
        {entries.map(([label, value], i) => (
          <div key={label} className="flex items-center gap-2">
            <span className="w-24 truncate text-right text-xs text-white/60">{label}</span>
            <div className="flex-1">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${max > 0 ? (value / max) * 100 : 0}%` }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className={`h-5 rounded ${color} flex items-center justify-end px-2`}
              >
                <span className="text-[10px] font-medium text-white">{value}</span>
              </motion.div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ClassificationView({ stats, results = [], filters = {}, onFilterChange }) {
  return (
    <div className="space-y-6">
      {/* Stats Charts */}
      <div className="grid gap-4 lg:grid-cols-3">
        <BarChart data={stats?.by_category} title="By Category" color="bg-electric" />
        <BarChart data={stats?.by_type} title="By Type" color="bg-purple" />
        <BarChart data={stats?.by_urgency} title="By Urgency" color="bg-orange-500" />
      </div>

      {/* Filters */}
      <div className="glass flex flex-wrap items-center gap-3 rounded-xl p-3">
        <select
          value={filters.category || ''}
          onChange={(e) => onFilterChange({ ...filters, category: e.target.value || undefined })}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
        >
          <option value="">All Categories</option>
          {stats?.by_category && Object.keys(stats.by_category).map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <select
          value={filters.urgency || ''}
          onChange={(e) => onFilterChange({ ...filters, urgency: e.target.value || undefined })}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
        >
          <option value="">All Urgency</option>
          {['Critical', 'High', 'Medium', 'Low'].map((u) => (
            <option key={u} value={u}>{u}</option>
          ))}
        </select>
        <select
          value={filters.email_type || ''}
          onChange={(e) => onFilterChange({ ...filters, email_type: e.target.value || undefined })}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
        >
          <option value="">All Types</option>
          {stats?.by_type && Object.keys(stats.by_type).map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Results List */}
      <div className="space-y-2">
        {results.length === 0 && (
          <p className="text-sm text-white/40">No classification results found.</p>
        )}
        {results.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.02 }}
            className="glass rounded-lg p-3"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs text-white/50">Email: {item.email_id}</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {item.category && (
                    <span className="rounded-full bg-electric/20 px-2 py-0.5 text-[10px] text-electric">{item.category}</span>
                  )}
                  {item.email_type && (
                    <span className="rounded-full bg-purple/20 px-2 py-0.5 text-[10px] text-purple-300">{item.email_type}</span>
                  )}
                  {item.urgency && (
                    <span className={`rounded-full px-2 py-0.5 text-[10px] text-white ${URGENCY_COLORS[item.urgency] || 'bg-gray-500'}`}>
                      {item.urgency}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                {item.sentiment && (
                  <span className={`text-xs ${SENTIMENT_COLORS[item.sentiment] || 'text-white/50'}`}>{item.sentiment}</span>
                )}
                {item.ai_confidence != null && (
                  <span className="text-[10px] text-white/30">{(item.ai_confidence * 100).toFixed(0)}% confidence</span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
