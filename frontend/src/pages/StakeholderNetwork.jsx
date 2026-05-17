import { useNavigate } from 'react-router-dom'
import NetworkGraph from '../components/stakeholders/NetworkGraph'
import Loading from '../components/ui/Loading'
import { useCommunicationNetwork } from '../hooks/useStakeholderData'

export default function StakeholderNetworkPage() {
  const navigate = useNavigate()
  const { network, loading, error, refresh } = useCommunicationNetwork()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/stakeholders')}
            className="text-sm text-white/50 transition hover:text-white"
          >
            ← Back to Stakeholders
          </button>
          <h2 className="mt-2 text-2xl font-semibold">Communication Network</h2>
          <p className="text-sm text-white/50">Visual map of stakeholder interactions</p>
        </div>
        <button
          onClick={refresh}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/20"
        >
          ↻ Refresh
        </button>
      </div>

      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      <NetworkGraph network={network} />
    </div>
  )
}
