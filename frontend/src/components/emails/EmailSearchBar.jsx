import { useState } from 'react'

export default function EmailSearchBar({ onSearch, loading = false }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass flex items-center gap-2 rounded-xl p-2">
      <span className="pl-2 text-white/40">🔍</span>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search emails by subject, sender, content..."
        className="flex-1 bg-transparent px-2 py-1.5 text-sm text-white placeholder-white/30 outline-none"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="rounded-lg bg-gradient-to-r from-electric to-purple px-4 py-1.5 text-xs font-medium text-white transition hover:scale-105 disabled:opacity-40"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  )
}
