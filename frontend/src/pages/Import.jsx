import { useMemo, useState } from 'react'
import { uploadMbox } from '../api/imports'
import ImportHistory from '../components/ImportHistory'
import PhaseStepper from '../components/PhaseStepper'
import StatsCard from '../components/StatsCard'
import ImportScene from '../components/three/ImportScene'
import { useImportProgress } from '../hooks/useImportProgress'

function formatEta(seconds) {
  if (!seconds && seconds !== 0) return '--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}

export default function ImportPage() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [activeJobId, setActiveJobId] = useState(null)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const { progress, percentage } = useImportProgress(activeJobId)

  const phase = progress.phase || (uploadProgress > 0 && uploadProgress < 100 ? 'uploading' : 'counting')

  const statCards = useMemo(
    () => [
      { label: 'Emails', value: `${progress.processed_emails}/${progress.total_emails || '--'}`, icon: '📨' },
      { label: 'Attachments', value: progress.total_attachments || 0, icon: '📎', accent: 'border-violet-400' },
      { label: 'Speed', value: `${progress.emails_per_second || 0} /s`, icon: '⚡', accent: 'border-amber-400' },
      { label: 'ETA', value: formatEta(progress.estimated_remaining_seconds), icon: '⏳', accent: 'border-emerald-400' },
    ],
    [progress],
  )

  const handleFile = async (file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.mbox')) {
      setError('Please select a .mbox file')
      return
    }

    setError('')
    setUploadProgress(0)
    try {
      const job = await uploadMbox(file, setUploadProgress)
      setActiveJobId(job.id)
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setError(err.message || 'Upload failed')
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">MBOX Import Engine</h2>

      <label className="glass block cursor-pointer rounded-xl border border-dashed border-cyan-300/60 p-10 text-center transition hover:border-cyan-200 hover:bg-white/15">
        <input type="file" accept=".mbox" className="hidden" onChange={(event) => handleFile(event.target.files?.[0])} />
        <p className="text-lg font-medium">Drop your MBOX file or click to choose</p>
        <p className="mt-2 text-sm text-white/70">Streaming upload with 10MB chunks for large files</p>
        <p className="mt-3 text-sm text-cyan-200">Upload progress: {uploadProgress}%</p>
      </label>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <div className="space-y-4">
          <ImportScene percentage={percentage || uploadProgress} />
          <PhaseStepper phase={phase} />
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-white/70">Current Subject</p>
            <p className="mt-1 truncate text-lg">{progress.current_subject || 'Waiting for import...'}</p>
            <p className="mt-2 text-sm text-white/60">
              Status: <span className="capitalize">{progress.status || 'pending'}</span>
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {statCards.map((card) => (
            <StatsCard key={card.label} {...card} />
          ))}
        </div>
      </div>

      <ImportHistory refreshKey={refreshKey} />
    </div>
  )
}
