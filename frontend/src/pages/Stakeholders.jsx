import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import StakeholderCard from '../components/stakeholders/StakeholderCard'
import StakeholderFilters from '../components/stakeholders/StakeholderFilters'
import HeatmapChart from '../components/stakeholders/HeatmapChart'
import Loading from '../components/ui/Loading'
import { useStakeholders } from '../hooks/useStakeholderData'

export default function Stakeholders() {
  const [filters, setFilters] = useState({})
  const [selectedIds, setSelectedIds] = useState([])
  const navigate = useNavigate()

  const apiFilters = useMemo(
    () => ({
      department: filters.department,
      role: filters.role,
      is_internal: filters.is_internal,
    }),
    [filters.department, filters.role, filters.is_internal]
  )
  const { stakeholders, stats, departments, loading, error, refresh } = useStakeholders(apiFilters)

  const filtered = useMemo(() => {
    if (!filters.search) return stakeholders
    const q = filters.search.toLowerCase()
    return stakeholders.filter(
      (s) =>
        (s.name || '').toLowerCase().includes(q) ||
        s.email_address.toLowerCase().includes(q) ||
        (s.department || '').toLowerCase().includes(q)
    )
  }, [stakeholders, filters.search])

  const toggleSelect = (id) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Stakeholders</h2>
          {stats && (
            <p className="text-sm text-white/50">{stats.total} total stakeholders</p>
          )}
        </div>
        <div className="flex gap-2">
          {selectedIds.length >= 2 && (
            <button
              onClick={() => navigate(`/stakeholders/compare?ids=${selectedIds.join(',')}`)}
              className="rounded-lg bg-gradient-to-r from-electric to-purple px-3 py-1.5 text-xs font-medium text-white transition hover:scale-105"
            >
              Compare ({selectedIds.length})
            </button>
          )}
          <button
            onClick={() => navigate('/stakeholders/network')}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
          >
            🔗 Network View
          </button>
          <button
            onClick={refresh}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      <StakeholderFilters departments={departments} filters={filters} onFilterChange={setFilters} />

      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      {/* Department Heatmap */}
      {stats?.by_department && <HeatmapChart data={stats.by_department} title="Stakeholders by Department" />}

      {/* Stakeholder Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((s, i) => (
          <StakeholderCard
            key={s.id}
            stakeholder={s}
            index={i}
            selected={selectedIds.includes(s.id)}
            onSelect={toggleSelect}
          />
        ))}
      </div>

      {!loading && filtered.length === 0 && (
        <p className="text-center text-sm text-white/40">No stakeholders found.</p>
      )}
    </div>
  )
}
