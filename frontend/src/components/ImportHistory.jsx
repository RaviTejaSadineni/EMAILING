import { useEffect, useState } from 'react'
import { getImportJobs, retryImport } from '../api/imports'

const statusClass = {
  pending: 'bg-white/20 text-white',
  processing: 'bg-cyan-500/25 text-cyan-200',
  completed: 'bg-emerald-500/25 text-emerald-200',
  failed: 'bg-rose-500/25 text-rose-200',
  cancelled: 'bg-amber-500/25 text-amber-200',
}

export default function ImportHistory({ refreshKey }) {
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    getImportJobs().then(setJobs).catch(() => setJobs([]))
  }, [refreshKey])

  const onRetry = async (id) => {
    await retryImport(id)
    const updated = await getImportJobs()
    setJobs(updated)
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-lg font-semibold">Import History</h3>
      <div className="mt-3 space-y-2">
        {jobs.map((job) => (
          <div key={job.id} className="rounded-lg border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between gap-4">
              <p className="truncate text-sm">{job.filename}</p>
              <span className={`rounded-full px-2 py-1 text-xs ${statusClass[job.status] || statusClass.pending}`}>
                {job.status}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/70">
              Emails: {job.processed_emails}/{job.total_emails} • Attachments: {job.total_attachments}
            </p>
            {job.status === 'failed' ? (
              <button
                type="button"
                onClick={() => onRetry(job.id)}
                className="mt-2 rounded-md bg-electric px-3 py-1 text-xs font-medium"
              >
                Retry
              </button>
            ) : null}
          </div>
        ))}
        {!jobs.length ? <p className="text-sm text-white/60">No import jobs yet.</p> : null}
      </div>
    </div>
  )
}
