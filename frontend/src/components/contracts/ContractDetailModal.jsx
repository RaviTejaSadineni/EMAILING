import { useContractDetail } from '../../hooks/useContractData'
import ContractTimeline from './ContractTimeline'
import Loading from '../ui/Loading'
import Modal from '../ui/Modal'

function riskLabel(score) {
  if (score == null) return { text: 'Unknown', color: 'text-white/40' }
  if (score >= 0.7) return { text: 'High', color: 'text-red-400' }
  if (score >= 0.4) return { text: 'Medium', color: 'text-yellow-400' }
  return { text: 'Low', color: 'text-green-400' }
}

export default function ContractDetailModal({ contractId, open, onClose }) {
  const { detail, timeline, clauses, stakeholders, loading, error } = useContractDetail(
    open ? contractId : null
  )

  return (
    <Modal open={open} title={detail?.agreement_name || 'Contract Detail'} onClose={onClose}>
      {loading && <Loading />}
      {error && <p className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</p>}

      {detail && (
        <div className="max-h-[70vh] space-y-5 overflow-y-auto pr-1">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-white/50">Type</p>
              <p className="text-sm text-white">{detail.agreement_type || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-white/50">Counterparty</p>
              <p className="text-sm text-white">{detail.counterparty_name || detail.counterparty_email || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-white/50">Current Stage</p>
              <p className="text-sm text-white">{detail.current_stage || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-white/50">Risk Score</p>
              <p className={`text-sm font-semibold ${riskLabel(detail.risk_score).color}`}>
                {detail.risk_score != null
                  ? `${(detail.risk_score * 100).toFixed(0)}% (${riskLabel(detail.risk_score).text})`
                  : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/50">Complexity</p>
              <p className="text-sm text-white">
                {detail.complexity_score != null ? `${(detail.complexity_score * 100).toFixed(0)}%` : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/50">SLA Status</p>
              <p className={`text-sm font-semibold ${detail.sla_breached ? 'text-red-400' : 'text-green-400'}`}>
                {detail.sla_breached ? 'Breached' : 'Compliant'}
              </p>
            </div>
          </div>

          {/* AI Summary */}
          {detail.ai_summary && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-white/60">AI Summary</p>
              <p className="rounded-lg bg-white/5 p-3 text-sm text-white/80">{detail.ai_summary}</p>
            </div>
          )}

          {/* Key Clauses */}
          {clauses && clauses.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-white/60">
                Key Clauses ({clauses.length})
              </p>
              <div className="space-y-2">
                {clauses.map((clause, i) => (
                  <div key={i} className="rounded-lg bg-white/5 p-3">
                    <p className="text-sm font-medium text-electric">{clause.type}</p>
                    {clause.evidence && (
                      <p className="mt-1 text-xs text-white/60">{clause.evidence}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Delay Reasons */}
          {detail.delay_reasons && detail.delay_reasons.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-white/60">
                Delay Reasons
              </p>
              <div className="space-y-2">
                {detail.delay_reasons.map((reason, i) => (
                  <div key={i} className="rounded-lg bg-red-500/10 p-3">
                    <p className="text-sm text-red-300">{reason.reason || reason.description || JSON.stringify(reason)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeline */}
          {timeline && <ContractTimeline timeline={timeline} />}

          {/* Stakeholders */}
          {stakeholders && stakeholders.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-white/60">
                Related Stakeholders
              </p>
              <div className="space-y-2">
                {stakeholders.map((s) => (
                  <div key={s.id} className="flex items-center gap-3 rounded-lg bg-white/5 p-3">
                    <div>
                      <p className="text-sm text-white">{s.name || s.email_address}</p>
                      <p className="text-xs text-white/50">{s.email_address}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
