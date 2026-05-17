import { CONTRACT_STAGES } from '../../utils/constants'

export default function ContractTimeline({ timeline }) {
  if (!timeline || !timeline.stage_history || timeline.stage_history.length === 0) {
    return (
      <p className="text-sm text-white/40">No timeline data available.</p>
    )
  }

  const completedStages = new Set(timeline.stage_history.map((s) => s.stage))

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-white/80">Stage Timeline</h4>
      <div className="relative">
        {CONTRACT_STAGES.map((stage, i) => {
          const entry = timeline.stage_history.find((s) => s.stage === stage)
          const isCompleted = completedStages.has(stage)

          return (
            <div key={stage} className="flex items-start gap-3 pb-4">
              {/* Connector line */}
              <div className="flex flex-col items-center">
                <div
                  className={`h-3 w-3 rounded-full border-2 ${
                    isCompleted
                      ? 'border-electric bg-electric'
                      : 'border-white/20 bg-transparent'
                  }`}
                />
                {i < CONTRACT_STAGES.length - 1 && (
                  <div
                    className={`w-0.5 flex-1 ${
                      isCompleted ? 'bg-electric/40' : 'bg-white/10'
                    }`}
                    style={{ minHeight: '24px' }}
                  />
                )}
              </div>
              {/* Stage info */}
              <div className="flex-1 -mt-0.5">
                <p className={`text-sm font-medium ${isCompleted ? 'text-white' : 'text-white/40'}`}>
                  {stage}
                </p>
                {entry && (
                  <p className="text-xs text-white/50">
                    {entry.entered_at
                      ? new Date(entry.entered_at).toLocaleDateString()
                      : ''}
                    {entry.duration_days != null && ` · ${entry.duration_days}d`}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
