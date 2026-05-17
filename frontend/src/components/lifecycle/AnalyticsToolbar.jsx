import { useState } from 'react'
import { CONTRACT_STAGES } from '../../utils/constants'

export default function AnalyticsToolbar({
  filters,
  onFilterChange,
  onReset,
  savedPresets = [],
  onApplyPreset,
  onSavePreset,
  onDeletePreset,
  onExport,
}) {
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [presetName, setPresetName] = useState('')

  const handleSave = () => {
    if (!presetName.trim()) return
    onSavePreset?.(presetName.trim())
    setPresetName('')
    setShowSaveDialog(false)
  }

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Search bar */}
        <div className="relative min-w-[200px] flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">🔍</span>
          <input
            type="text"
            placeholder="Search analytics…"
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
            className="w-full rounded-lg border border-white/20 bg-white/10 py-2 pl-9 pr-3 text-sm text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-electric"
          />
        </div>

        {/* Date range */}
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => onFilterChange('dateFrom', e.target.value)}
          className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-electric"
          title="From date"
        />
        <input
          type="date"
          value={filters.dateTo}
          onChange={(e) => onFilterChange('dateTo', e.target.value)}
          className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-electric"
          title="To date"
        />

        {/* Department filter */}
        <select
          value={filters.department}
          onChange={(e) => onFilterChange('department', e.target.value)}
          className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-electric"
        >
          <option value="">All Departments</option>
          <option value="Legal">Legal</option>
          <option value="Finance">Finance</option>
          <option value="Procurement">Procurement</option>
          <option value="Compliance">Compliance</option>
          <option value="Operations">Operations</option>
          <option value="Sales">Sales</option>
        </select>

        {/* Stage filter */}
        <select
          value={filters.stage}
          onChange={(e) => onFilterChange('stage', e.target.value)}
          className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-electric"
        >
          <option value="">All Stages</option>
          {CONTRACT_STAGES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        {/* Saved presets dropdown */}
        {savedPresets.length > 0 && (
          <select
            defaultValue=""
            onChange={(e) => {
              const preset = savedPresets.find((p) => p.id === e.target.value)
              if (preset) onApplyPreset?.(preset)
              e.target.value = ''
            }}
            className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-electric"
          >
            <option value="" disabled>
              Load Preset…
            </option>
            {savedPresets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}

        {/* Action buttons */}
        <button
          onClick={() => setShowSaveDialog(true)}
          className="rounded-lg bg-white/10 px-3 py-2 text-xs text-white/70 transition hover:bg-white/20"
          title="Save current filters as preset"
        >
          💾 Save
        </button>
        <button
          onClick={onExport}
          className="rounded-lg bg-white/10 px-3 py-2 text-xs text-white/70 transition hover:bg-white/20"
          title="Export data as CSV"
        >
          📥 Export
        </button>
        <button
          onClick={onReset}
          className="rounded-lg bg-white/10 px-3 py-2 text-xs text-white/70 transition hover:bg-white/20"
          title="Reset all filters"
        >
          ↻ Reset
        </button>
      </div>

      {/* Saved presets pills (for quick delete) */}
      {savedPresets.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {savedPresets.map((p) => (
            <span
              key={p.id}
              className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1 text-[10px] text-white/60"
            >
              {p.name}
              <button
                onClick={() => onDeletePreset?.(p.id)}
                className="ml-0.5 text-white/40 hover:text-red-400"
                title="Delete preset"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Save dialog */}
      {showSaveDialog && (
        <div className="mt-3 flex items-center gap-2">
          <input
            type="text"
            placeholder="Preset name…"
            value={presetName}
            onChange={(e) => setPresetName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            className="flex-1 rounded-lg border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-electric"
            autoFocus
          />
          <button
            onClick={handleSave}
            className="rounded-lg bg-gradient-to-r from-electric to-purple px-3 py-1.5 text-xs font-semibold text-white"
          >
            Save
          </button>
          <button
            onClick={() => setShowSaveDialog(false)}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
