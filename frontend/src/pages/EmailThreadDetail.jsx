import { useParams, useNavigate } from 'react-router-dom'
import ThreadViewer from '../components/emails/ThreadViewer'
import Loading from '../components/ui/Loading'
import { useThreadDetail } from '../hooks/useEmailData'

export default function EmailThreadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { thread, loading, error } = useThreadDetail(id)

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/emails')}
        className="text-sm text-white/50 transition hover:text-white"
      >
        ← Back to Emails
      </button>

      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      <ThreadViewer thread={thread} />
    </div>
  )
}
