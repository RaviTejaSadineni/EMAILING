import { useSearchParams, useNavigate } from 'react-router-dom'
import ComparisonTable from '../components/stakeholders/ComparisonTable'
import Loading from '../components/ui/Loading'
import { useStakeholderComparison } from '../hooks/useStakeholderData'

export default function StakeholderComparisonPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const idsParam = searchParams.get('ids') || ''
  const ids = idsParam.split(',').filter(Boolean)

  const { comparison, loading, error } = useStakeholderComparison(ids)

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
          <h2 className="mt-2 text-2xl font-semibold">Stakeholder Comparison</h2>
          <p className="text-sm text-white/50">Comparing {ids.length} stakeholders</p>
        </div>
      </div>

      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      <ComparisonTable comparison={comparison} />

      {ids.length < 2 && (
        <div className="glass rounded-xl p-6 text-center">
          <p className="text-white/50">Select at least 2 stakeholders from the stakeholders list to compare.</p>
          <button
            onClick={() => navigate('/stakeholders')}
            className="mt-3 rounded-lg bg-gradient-to-r from-electric to-purple px-4 py-2 text-sm font-medium text-white transition hover:scale-105"
          >
            Go to Stakeholders
          </button>
        </div>
      )}
    </div>
  )
}
