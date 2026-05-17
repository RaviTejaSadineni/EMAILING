import { useState, useMemo } from 'react'
import ContractCard from '../components/contracts/ContractCard'
import ContractFilters from '../components/contracts/ContractFilters'
import ContractStats from '../components/contracts/ContractStats'
import ContractDetailModal from '../components/contracts/ContractDetailModal'
import Loading from '../components/ui/Loading'
import { useContracts, useContractExtraction } from '../hooks/useContractData'

export default function Contracts() {
  const [filters, setFilters] = useState({})
  const [selectedId, setSelectedId] = useState(null)

  const apiFilters = useMemo(
    () => ({
      agreement_type: filters.agreement_type,
      counterparty: filters.counterparty,
      stage: filters.stage,
    }),
    [filters.agreement_type, filters.counterparty, filters.stage]
  )

  const { contracts, stats, loading, error, refresh } = useContracts(apiFilters)
  const { status: extractionStatus, loading: extracting, start: startExtraction, checkStatus } = useContractExtraction()

  // Derive agreement types from stats for the filter dropdown
  const agreementTypes = useMemo(
    () => (stats?.by_type ? Object.keys(stats.by_type) : []),
    [stats]
  )

  // Client-side search filter
  const filtered = useMemo(() => {
    if (!filters.search) return contracts
    const q = filters.search.toLowerCase()
    return contracts.filter(
      (c) =>
        (c.agreement_name || '').toLowerCase().includes(q) ||
        (c.counterparty_name || '').toLowerCase().includes(q) ||
        (c.counterparty_email || '').toLowerCase().includes(q) ||
        (c.agreement_type || '').toLowerCase().includes(q)
    )
  }, [contracts, filters.search])

  const handleExtract = async () => {
    await startExtraction()
    // Poll status after a brief delay
    setTimeout(checkStatus, 2000)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Contracts</h2>
          {stats && (
            <p className="text-sm text-white/50">{stats.total_contracts} total contracts</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="rounded-lg bg-gradient-to-r from-electric to-purple px-3 py-1.5 text-xs font-medium text-white transition hover:scale-105 disabled:opacity-50"
          >
            {extracting ? '⏳ Extracting…' : '🔄 Extract Contracts'}
          </button>
          <button
            onClick={refresh}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Extraction Status */}
      {extractionStatus && extractionStatus.status === 'in_progress' && (
        <div className="glass rounded-xl p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/70">
              ⏳ Extraction in progress: {extractionStatus.processed_items}/{extractionStatus.total_items} items
            </span>
            <span className="text-electric">{extractionStatus.progress}%</span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-electric transition-all"
              style={{ width: `${extractionStatus.progress || 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats */}
      <ContractStats stats={stats} />

      {/* Type Distribution */}
      {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
        <div className="glass rounded-xl p-4">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/60">
            By Agreement Type
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <button
                key={type}
                onClick={() =>
                  setFilters((f) => ({
                    ...f,
                    agreement_type: f.agreement_type === type ? undefined : type,
                  }))
                }
                className={`rounded-full px-3 py-1 text-xs transition ${
                  filters.agreement_type === type
                    ? 'bg-electric/30 text-white'
                    : 'bg-white/10 text-white/60 hover:bg-white/20'
                }`}
              >
                {type} ({count})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <ContractFilters
        filters={filters}
        agreementTypes={agreementTypes}
        onFilterChange={setFilters}
      />

      {/* Loading & Error */}
      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      {/* Contract Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((c, i) => (
          <ContractCard
            key={c.id}
            contract={c}
            index={i}
            onClick={setSelectedId}
          />
        ))}
      </div>

      {!loading && filtered.length === 0 && (
        <p className="text-center text-sm text-white/40">
          No contracts found.{' '}
          {contracts.length === 0 && 'Try running contract extraction first.'}
        </p>
      )}

      {/* Detail Modal */}
      <ContractDetailModal
        contractId={selectedId}
        open={!!selectedId}
        onClose={() => setSelectedId(null)}
      />
    </div>
  )
}
