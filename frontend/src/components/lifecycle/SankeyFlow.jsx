import { motion } from 'framer-motion'
import { CONTRACT_STAGES } from '../../utils/constants'

const STAGE_COLORS = [
  '#3b82f6', '#8b5cf6', '#a855f7', '#d946ef', '#f43f5e', '#f59e0b', '#10b981',
]

export default function SankeyFlow({ transitions = [] }) {
  if (!transitions.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Stage Flow (Sankey)</p>
        <p className="mt-4 text-sm text-white/40">No transition data available</p>
      </div>
    )
  }

  const stageIndex = {}
  CONTRACT_STAGES.forEach((s, i) => {
    stageIndex[s] = i
  })

  const maxCount = Math.max(...transitions.map((t) => t.count), 1)
  const svgWidth = 700
  const svgHeight = 320
  const leftX = 60
  const rightX = svgWidth - 60
  const stageSpacing = svgHeight / (CONTRACT_STAGES.length + 1)

  const getY = (stageIdx) => stageSpacing * (stageIdx + 1)

  return (
    <div className="glass card-3d rounded-2xl p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-wider text-white/60">Stage Flow (Sankey)</p>
      <div className="overflow-x-auto">
        <svg width={svgWidth} height={svgHeight} className="mx-auto">
          {/* Stage labels on left */}
          {CONTRACT_STAGES.map((stage, i) => (
            <g key={`left-${stage}`}>
              <circle cx={leftX} cy={getY(i)} r={6} fill={STAGE_COLORS[i]} opacity={0.8} />
              <text x={leftX - 12} y={getY(i) + 4} textAnchor="end" className="fill-white/60 text-[9px]">
                {stage.length > 15 ? stage.slice(0, 15) + '…' : stage}
              </text>
            </g>
          ))}

          {/* Stage labels on right */}
          {CONTRACT_STAGES.map((stage, i) => (
            <g key={`right-${stage}`}>
              <circle cx={rightX} cy={getY(i)} r={6} fill={STAGE_COLORS[i]} opacity={0.8} />
              <text x={rightX + 12} y={getY(i) + 4} textAnchor="start" className="fill-white/60 text-[9px]">
                {stage.length > 15 ? stage.slice(0, 15) + '…' : stage}
              </text>
            </g>
          ))}

          {/* Flow lines */}
          {transitions.map((t, i) => {
            const fromIdx = stageIndex[t.from_stage]
            const toIdx = stageIndex[t.to_stage]
            if (fromIdx === undefined || toIdx === undefined) return null

            const thickness = Math.max((t.count / maxCount) * 12, 1.5)
            const fromY = getY(fromIdx)
            const toY = getY(toIdx)
            const midX = (leftX + rightX) / 2
            const fromColor = STAGE_COLORS[fromIdx % STAGE_COLORS.length]

            return (
              <motion.path
                key={i}
                d={`M ${leftX + 8} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${rightX - 8} ${toY}`}
                fill="none"
                stroke={fromColor}
                strokeWidth={thickness}
                opacity={0.5}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.8, delay: i * 0.05 }}
              />
            )
          })}
        </svg>
      </div>
    </div>
  )
}
