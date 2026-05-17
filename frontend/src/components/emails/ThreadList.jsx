import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

export default function ThreadList({ threads = [], total = 0, page = 1, pageSize = 20, onPageChange }) {
  const navigate = useNavigate()
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-2">
      {threads.map((thread, i) => (
        <motion.div
          key={thread.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.02 }}
          onClick={() => navigate(`/emails/threads/${thread.id}`)}
          className="glass cursor-pointer rounded-lg p-3 transition hover:bg-white/15"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h4 className="truncate text-sm font-medium text-white">{thread.thread_subject}</h4>
              {thread.merged_subject && thread.merged_subject !== thread.thread_subject && (
                <p className="truncate text-xs text-white/40">aka: {thread.merged_subject}</p>
              )}
              <div className="mt-1 flex flex-wrap gap-1.5">
                {thread.participant_emails?.slice(0, 3).map((email) => (
                  <span key={email} className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-white/50">{email}</span>
                ))}
                {(thread.participant_emails?.length || 0) > 3 && (
                  <span className="text-[10px] text-white/30">+{thread.participant_emails.length - 3} more</span>
                )}
              </div>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <span className="rounded-full bg-electric/20 px-2 py-0.5 text-[10px] font-medium text-electric">
                {thread.email_count} emails
              </span>
              {thread.ai_confidence != null && (
                <span className="text-[10px] text-white/30">{(thread.ai_confidence * 100).toFixed(0)}% conf</span>
              )}
              {thread.last_date && (
                <span className="text-[10px] text-white/30">{new Date(thread.last_date).toLocaleDateString()}</span>
              )}
            </div>
          </div>
        </motion.div>
      ))}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-3">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="rounded-lg bg-white/10 px-3 py-1 text-xs text-white/70 transition hover:bg-white/20 disabled:opacity-30"
          >
            ← Prev
          </button>
          <span className="text-xs text-white/50">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="rounded-lg bg-white/10 px-3 py-1 text-xs text-white/70 transition hover:bg-white/20 disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
