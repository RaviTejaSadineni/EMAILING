const phases = ['uploading', 'counting', 'parsing', 'storing_attachments', 'complete']

const labels = {
  uploading: 'Upload',
  counting: 'Count',
  parsing: 'Parse',
  storing_attachments: 'Store',
  complete: 'Complete',
}

export default function PhaseStepper({ phase }) {
  const activeIndex = Math.max(phases.indexOf(phase), 0)

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2">
        {phases.map((key, index) => {
          const done = index < activeIndex
          const active = index === activeIndex
          return (
            <div key={key} className="flex flex-1 items-center gap-2">
              <div
                className={`h-8 w-8 rounded-full border text-center text-xs leading-8 ${
                  done
                    ? 'border-emerald-400 bg-emerald-400/30 text-emerald-200'
                    : active
                      ? 'border-cyan-300 bg-cyan-300/30 text-cyan-100 animate-pulse'
                      : 'border-white/30 text-white/60'
                }`}
              >
                {done ? '✓' : index + 1}
              </div>
              <span className={`text-xs ${active ? 'text-white' : 'text-white/70'}`}>{labels[key]}</span>
              {index !== phases.length - 1 ? <div className="h-px flex-1 bg-white/25" /> : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
