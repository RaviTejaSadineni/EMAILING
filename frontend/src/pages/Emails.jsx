import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import ThreadList from '../components/emails/ThreadList'
import EmailSearchBar from '../components/emails/EmailSearchBar'
import ClassificationView from '../components/emails/ClassificationView'
import Loading from '../components/ui/Loading'
import { useThreads, useClassification, useEmailSearch } from '../hooks/useEmailData'

const TABS = [
  { key: 'threads', label: 'Threads', path: '/emails' },
  { key: 'classification', label: 'Classification', path: '/emails/classification' },
]

export default function Emails() {
  const location = useLocation()
  const isClassification = location.pathname.includes('/classification')
  const activeTab = isClassification ? 'classification' : 'threads'

  const [threadPage, setThreadPage] = useState(1)
  const [classFilters, setClassFilters] = useState({})

  const { threads, total, stats: threadStats, loading: threadsLoading, error: threadsError } = useThreads(threadPage)
  const { results: classResults, stats: classStats, loading: classLoading, error: classError } = useClassification(classFilters)
  const { results: searchResults, loading: searchLoading, search, clear: clearSearch } = useEmailSearch()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Email Browser</h2>
          {threadStats && (
            <p className="text-sm text-white/50">
              {threadStats.total_threads} threads • {threadStats.avg_emails_per_thread.toFixed(1)} avg emails/thread
            </p>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="glass flex rounded-xl p-1">
        {TABS.map((tab) => (
          <NavLink
            key={tab.key}
            to={tab.path}
            end={tab.key === 'threads'}
            className={({ isActive }) =>
              `flex-1 rounded-lg px-4 py-2 text-center text-sm font-medium transition ${
                (tab.key === activeTab) ? 'bg-electric/30 text-white' : 'text-white/50 hover:text-white/70'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </div>

      {/* Search */}
      <EmailSearchBar onSearch={search} loading={searchLoading} />

      {/* Search Results */}
      {searchResults && (
        <div className="glass rounded-xl p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wider text-white/60">
              Search Results ({searchResults.total || 0})
            </p>
            <button
              onClick={clearSearch}
              className="text-xs text-white/40 hover:text-white/60"
            >
              Clear
            </button>
          </div>
          <div className="space-y-2">
            {(searchResults.emails || searchResults.items || []).map((item, i) => (
              <div key={item.id || i} className="rounded-lg bg-white/5 p-3">
                <p className="text-sm text-white/80">{item.subject || item.title || item.email || 'Untitled'}</p>
                <p className="text-xs text-white/40">{item.from_address || item.type || ''}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'threads' && (
        <>
          {threadsLoading && <Loading />}
          {threadsError && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{threadsError}</p>}
          <ThreadList threads={threads} total={total} page={threadPage} onPageChange={setThreadPage} />
        </>
      )}

      {activeTab === 'classification' && (
        <>
          {classLoading && <Loading />}
          {classError && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{classError}</p>}
          <ClassificationView
            stats={classStats}
            results={classResults}
            filters={classFilters}
            onFilterChange={setClassFilters}
          />
        </>
      )}
    </div>
  )
}
