import { CONTRACT_STAGES } from '../../utils/constants'

export default function ContractFilters({ filters = {}, agreementTypes = [], onFilterChange }) {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value || undefined })
  }

  return (
    <div className="glass flex flex-wrap items-center gap-3 rounded-xl p-3">
      <select
        value={filters.agreement_type || ''}
        onChange={(e) => handleChange('agreement_type', e.target.value)}
        className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
      >
        <option value="">All Types</option>
        {agreementTypes.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
      <select
        value={filters.stage || ''}
        onChange={(e) => handleChange('stage', e.target.value)}
        className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
      >
        <option value="">All Stages</option>
        {CONTRACT_STAGES.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Search by counterparty..."
        value={filters.counterparty || ''}
        onChange={(e) => handleChange('counterparty', e.target.value)}
        className="flex-1 rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white placeholder-white/30 outline-none"
      />
      <input
        type="text"
        placeholder="Search contracts..."
        value={filters.search || ''}
        onChange={(e) => handleChange('search', e.target.value)}
        className="flex-1 rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white placeholder-white/30 outline-none"
      />
    </div>
  )
}
