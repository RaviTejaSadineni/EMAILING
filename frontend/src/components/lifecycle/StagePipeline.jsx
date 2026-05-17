import { motion } from 'framer-motion'
import { CONTRACT_STAGES } from '../../utils/constants'

const STAGE_COLORS = [
  '#3b82f6', '#8b5cf6', '#a855f7', '#d946ef', '#f43f5e', '#f59e0b', '#10b981',
]

export default function StagePipeline({ stageDistribution }) {
  const stages = CONTRACT_STAGES.map((stageName, i) => {
    const item = stageDistribution?.items?.find((d) => d.label === stageName)
    return {
      name: stageName,
      count: item?.count || 0,
      percentage: item?.percentage || 0,
      color: STAGE_COLORS[i % STAGE_COLORS.length],
    }
  })

  const maxCount = Math.max(...stages.map((s) => s.count), 1)

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Contract Stage Pipeline</p>
      <div className="flex items-end gap-2">
        {stages.map((stage, i) => (
          <motion.div
            key={stage.name}
            initial={{ opacity: 0, scaleY: 0 }}
            animate={{ opacity: 1, scaleY: 1 }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="group relative flex flex-1 origin-bottom flex-col items-center"
          >
            {/* Bar */}
            <div className="relative w-full">
              <div
                className="mx-auto w-full max-w-[48px] rounded-t-lg transition-all duration-300 group-hover:opacity-100"
                style={{
                  height: `${Math.max((stage.count / maxCount) * 120, 8)}px`,
                  background: `linear-gradient(to top, ${stage.color}66, ${stage.color})`,
                  opacity: 0.85,
                  boxShadow: `0 0 20px ${stage.color}33`,
                }}
              />
              {/* Count badge */}
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-sm font-bold" style={{ color: stage.color }}>
                {stage.count}
              </div>
            </div>
            {/* Label */}
            <p className="mt-2 w-full text-center text-[9px] leading-tight text-white/50">{stage.name}</p>
            {/* Connector arrow */}
            {i < stages.length - 1 && (
              <div className="absolute -right-2 top-1/2 text-white/20">→</div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
