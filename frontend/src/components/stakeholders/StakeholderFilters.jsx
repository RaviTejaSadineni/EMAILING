export default function StakeholderFilters({ departments = [], filters = {}, onFilterChange }) {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value || undefined })
  }

  return (
    <div className="glass flex flex-wrap items-center gap-3 rounded-xl p-3">
      <select
        value={filters.department || ''}
        onChange={(e) => handleChange('department', e.target.value)}
        className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
      >
        <option value="">All Departments</option>
        {departments.map((d) => (
          <option key={d.department} value={d.department}>{d.department} ({d.count})</option>
        ))}
      </select>
      <select
        value={filters.is_internal === true ? 'true' : filters.is_internal === false ? 'false' : ''}
        onChange={(e) => handleChange('is_internal', e.target.value === '' ? null : e.target.value === 'true')}
        className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white outline-none"
      >
        <option value="">All Types</option>
        <option value="true">Internal</option>
        <option value="false">External</option>
      </select>
      <input
        type="text"
        placeholder="Search stakeholders..."
        value={filters.search || ''}
        onChange={(e) => handleChange('search', e.target.value)}
        className="flex-1 rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white placeholder-white/30 outline-none"
      />
    </div>
  )
}
