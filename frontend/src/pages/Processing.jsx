import { useCallback } from 'react'
import {
  getClassificationStatus,
  getContractExtractionStatus,
  getLifecycleStatus,
  getStakeholderExtractionStatus,
  getThreadMergeStatus,
  startClassification,
  startContractExtraction,
  startLifecycleDetection,
  startStakeholderExtraction,
  startThreadMerge,
} from '../api/processing'
import { useProcessingProgress } from '../hooks/useProcessingProgress'

function statusClass(status) {
  if (status === 'completed') return 'bg-emerald-500/20 text-emerald-200'
  if (status === 'in_progress') return 'bg-sky-500/20 text-sky-200 animate-pulse'
  if (status === 'failed') return 'bg-rose-500/20 text-rose-200'
  return 'bg-slate-500/20 text-slate-200'
}

function StepCard({ icon, title, description, status, percentage, onStart, disabled, summary }) {
  return (
    <div className="glass rounded-2xl p-5 shadow-[0_12px_30px_rgba(0,0,0,0.25)]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="text-sm text-white/70">{description}</p>
          </div>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClass(status)}`}>{status || 'not_started'}</span>
      </div>

      {status === 'in_progress' ? (
        <div className="mt-4">
          <div className="h-2 w-full overflow-hidden rounded bg-white/15">
            <div className="h-2 rounded bg-cyan-300 transition-all" style={{ width: `${percentage}%` }} />
          </div>
          <p className="mt-2 text-xs text-white/70">{Math.round(percentage)}% complete</p>
        </div>
      ) : null}

      {summary ? <p className="mt-3 text-sm text-white/80">{summary}</p> : null}

      <button
        type="button"
        disabled={disabled}
        onClick={onStart}
        className="mt-4 rounded-xl border border-cyan-300/40 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Start
      </button>
    </div>
  )
}

export default function ProcessingPage() {
  const classification = useProcessingProgress(getClassificationStatus)
  const merge = useProcessingProgress(getThreadMergeStatus)
  const contracts = useProcessingProgress(getContractExtractionStatus)
  const stakeholders = useProcessingProgress(getStakeholderExtractionStatus)
  const lifecycle = useProcessingProgress(getLifecycleStatus)

  const onStartClassification = useCallback(async () => classification.setStatus(await startClassification()), [classification])
  const onStartMerge = useCallback(async () => merge.setStatus(await startThreadMerge()), [merge])
  const onStartContracts = useCallback(async () => contracts.setStatus(await startContractExtraction()), [contracts])
  const onStartStakeholders = useCallback(async () => stakeholders.setStatus(await startStakeholderExtraction()), [stakeholders])
  const onStartLifecycle = useCallback(async () => lifecycle.setStatus(await startLifecycleDetection()), [lifecycle])

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">AI Processing Pipeline</h2>
      <p className="text-sm text-white/75">In production, these steps run automatically after import.</p>
      <div className="grid gap-4">
        <StepCard
          icon="🧠"
          title="Classify Emails"
          description="Category, type, urgency, sentiment"
          status={classification.status?.status}
          percentage={classification.percentage}
          onStart={onStartClassification}
          summary={classification.status ? `${classification.status.processed_items || 0}/${classification.status.total_items || 0} emails classified` : ''}
        />
        <StepCard
          icon="🧵"
          title="Merge Threads"
          description="Deterministic + AI fuzzy merge"
          status={merge.status?.status}
          percentage={merge.percentage}
          disabled={classification.status?.status !== 'completed'}
          onStart={onStartMerge}
          summary={merge.status ? `${merge.status.processed_items || 0}/${merge.status.total_items || 0} groups merged` : ''}
        />
        <StepCard
          icon="📄"
          title="Extract Contracts"
          description="Agreement metadata and clauses"
          status={contracts.status?.status}
          percentage={contracts.percentage}
          disabled={merge.status?.status !== 'completed'}
          onStart={onStartContracts}
          summary={contracts.status ? `${contracts.status.processed_items || 0}/${contracts.status.total_items || 0} contracts extracted` : ''}
        />
        <StepCard
          icon="👥"
          title="Profile Stakeholders"
          description="Department, role, influence"
          status={stakeholders.status?.status}
          percentage={stakeholders.percentage}
          disabled={contracts.status?.status !== 'completed'}
          onStart={onStartStakeholders}
          summary={stakeholders.status ? `${stakeholders.status.processed_items || 0}/${stakeholders.status.total_items || 0} stakeholders profiled` : ''}
        />
        <StepCard
          icon="⏱️"
          title="Detect Lifecycle"
          description="Stage assignment and bottlenecks"
          status={lifecycle.status?.status}
          percentage={lifecycle.percentage}
          disabled={stakeholders.status?.status !== 'completed'}
          onStart={onStartLifecycle}
          summary={lifecycle.status ? `${lifecycle.status.processed_items || 0}/${lifecycle.status.total_items || 0} contracts staged` : ''}
        />
        <StepCard
          icon="📈"
          title="Generate Analytics"
          description="Advanced analytics (coming soon)"
          status="not_started"
          percentage={0}
          disabled
          onStart={() => {}}
          summary="Placeholder for next implementation step"
        />
      </div>
    </div>
  )
}
