import { motion } from 'framer-motion'

export default function ThreadViewer({ thread }) {
  if (!thread) return null

  const emails = thread.emails || []

  return (
    <div className="space-y-4">
      <div className="glass rounded-xl p-4">
        <h3 className="text-lg font-semibold text-white">{thread.thread_subject}</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="rounded-full bg-electric/20 px-2.5 py-0.5 text-xs text-electric">
            {thread.email_count} emails
          </span>
          <span className="rounded-full bg-purple/20 px-2.5 py-0.5 text-xs text-purple-300">
            {thread.participant_emails?.length || 0} participants
          </span>
          {thread.first_date && (
            <span className="text-xs text-white/40">
              {new Date(thread.first_date).toLocaleDateString()} — {thread.last_date ? new Date(thread.last_date).toLocaleDateString() : 'ongoing'}
            </span>
          )}
        </div>
      </div>

      <div className="relative ml-4 border-l border-white/10 pl-6">
        {emails.map((email, i) => (
          <motion.div
            key={email.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="relative mb-4"
          >
            {/* Timeline dot */}
            <div className="absolute -left-[31px] top-3 h-3 w-3 rounded-full border-2 border-electric bg-navy" />

            <div className="glass rounded-lg p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-white">{email.from_address}</p>
                  <p className="text-[11px] text-white/40">
                    To: {Array.isArray(email.to_addresses) ? email.to_addresses.join(', ') : email.to_addresses}
                  </p>
                  {email.cc_addresses?.length > 0 && (
                    <p className="text-[11px] text-white/30">
                      CC: {Array.isArray(email.cc_addresses) ? email.cc_addresses.join(', ') : email.cc_addresses}
                    </p>
                  )}
                </div>
                <span className="shrink-0 text-[11px] text-white/30">
                  {email.date ? new Date(email.date).toLocaleString() : '—'}
                </span>
              </div>
              {email.subject && (
                <p className="mt-2 text-xs text-white/60">Subject: {email.subject}</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
