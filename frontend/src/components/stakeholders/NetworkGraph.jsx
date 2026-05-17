import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

const DEPT_COLORS = {
  Legal: '#667eea',
  Finance: '#f59e0b',
  Procurement: '#10b981',
  Engineering: '#ef4444',
  Sales: '#8b5cf6',
  HR: '#ec4899',
  default: '#94a3b8',
}

function getDeptColor(dept) {
  return DEPT_COLORS[dept] || DEPT_COLORS.default
}

export default function NetworkGraph({ network }) {
  const canvasRef = useRef(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const hoveredNodeRef = useRef(null)
  const nodesRef = useRef([])
  const edgesRef = useRef([])
  const animRef = useRef(null)

  useEffect(() => {
    if (!network?.nodes?.length) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const width = canvas.offsetWidth
    const height = canvas.offsetHeight
    canvas.width = width * 2
    canvas.height = height * 2
    ctx.scale(2, 2)

    // Initialize node positions
    const nodes = network.nodes.map((n, i) => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * width * 0.6,
      y: height / 2 + (Math.random() - 0.5) * height * 0.6,
      vx: 0,
      vy: 0,
      radius: Math.min(8 + (n.total_interactions || 1) * 0.5, 25),
    }))
    nodesRef.current = nodes

    const nodeMap = {}
    nodes.forEach((n) => { nodeMap[n.stakeholder_id] = n })

    const edges = (network.edges || []).map((e) => ({
      ...e,
      sourceNode: nodeMap[e.source],
      targetNode: nodeMap[e.target],
    })).filter((e) => e.sourceNode && e.targetNode)
    edgesRef.current = edges

    let iterations = 0
    const maxIterations = 200

    function simulate() {
      if (iterations > maxIterations) {
        draw()
        return
      }
      iterations++
      const alpha = 1 - iterations / maxIterations

      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          let dx = nodes[j].x - nodes[i].x
          let dy = nodes[j].y - nodes[i].y
          let dist = Math.sqrt(dx * dx + dy * dy) || 1
          let force = (150 * alpha) / dist
          nodes[i].vx -= (dx / dist) * force
          nodes[i].vy -= (dy / dist) * force
          nodes[j].vx += (dx / dist) * force
          nodes[j].vy += (dy / dist) * force
        }
      }

      // Attraction (edges)
      for (const e of edges) {
        let dx = e.targetNode.x - e.sourceNode.x
        let dy = e.targetNode.y - e.sourceNode.y
        let dist = Math.sqrt(dx * dx + dy * dy) || 1
        let force = (dist - 80) * 0.01 * alpha
        e.sourceNode.vx += (dx / dist) * force
        e.sourceNode.vy += (dy / dist) * force
        e.targetNode.vx -= (dx / dist) * force
        e.targetNode.vy -= (dy / dist) * force
      }

      // Center gravity
      for (const n of nodes) {
        n.vx += (width / 2 - n.x) * 0.001
        n.vy += (height / 2 - n.y) * 0.001
        n.vx *= 0.9
        n.vy *= 0.9
        n.x += n.vx
        n.y += n.vy
        n.x = Math.max(n.radius, Math.min(width - n.radius, n.x))
        n.y = Math.max(n.radius, Math.min(height - n.radius, n.y))
      }

      draw()
      animRef.current = requestAnimationFrame(simulate)
    }

    function draw() {
      ctx.clearRect(0, 0, width, height)

      // Draw edges
      for (const e of edges) {
        ctx.beginPath()
        ctx.moveTo(e.sourceNode.x, e.sourceNode.y)
        ctx.lineTo(e.targetNode.x, e.targetNode.y)
        ctx.strokeStyle = `rgba(102, 126, 234, ${Math.min(0.1 + (e.weight || 1) * 0.05, 0.6)})`
        ctx.lineWidth = Math.min(1 + (e.weight || 1) * 0.3, 4)
        ctx.stroke()
      }

      // Draw nodes
      for (const n of nodes) {
        const color = getDeptColor(n.department)
        const isHovered = hoveredNodeRef.current === n.stakeholder_id

        ctx.beginPath()
        ctx.arc(n.x, n.y, n.radius * (isHovered ? 1.3 : 1), 0, Math.PI * 2)
        ctx.fillStyle = color + (isHovered ? 'cc' : '88')
        ctx.fill()
        ctx.strokeStyle = color
        ctx.lineWidth = isHovered ? 2 : 1
        ctx.stroke()

        // Label
        const label = n.name || n.email?.split('@')[0] || ''
        if (label && (n.radius > 10 || isHovered)) {
          ctx.fillStyle = 'rgba(255,255,255,0.8)'
          ctx.font = `${isHovered ? 11 : 9}px Inter, sans-serif`
          ctx.textAlign = 'center'
          ctx.fillText(label, n.x, n.y + n.radius + 12)
        }
      }
    }

    simulate()

    // Mouse hover
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect()
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top
      let found = null
      for (const n of nodes) {
        const dist = Math.sqrt((mx - n.x) ** 2 + (my - n.y) ** 2)
        if (dist < n.radius * 1.5) {
          found = n.stakeholder_id
          break
        }
      }
      hoveredNodeRef.current = found
      setHoveredNode(found)
      canvas.style.cursor = found ? 'pointer' : 'default'
      draw()
    }

    canvas.addEventListener('mousemove', handleMouseMove)

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      canvas.removeEventListener('mousemove', handleMouseMove)
    }
  }, [network])

  if (!network?.nodes?.length) {
    return (
      <div className="glass card-3d rounded-2xl p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Communication Network</p>
        <p className="mt-4 text-sm text-white/40">No network data available</p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass card-3d rounded-2xl p-5"
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-white/60">Communication Network</p>
        <div className="flex gap-2">
          {Object.entries(DEPT_COLORS).filter(([k]) => k !== 'default').map(([dept, color]) => (
            <span key={dept} className="flex items-center gap-1 text-[10px] text-white/50">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {dept}
            </span>
          ))}
        </div>
      </div>
      <canvas
        ref={canvasRef}
        className="h-[400px] w-full rounded-lg"
      />
      {hoveredNode && (() => {
        const node = nodesRef.current.find((n) => n.stakeholder_id === hoveredNode)
        if (!node) return null
        return (
          <div className="mt-2 rounded-lg bg-white/5 p-2 text-xs text-white/70">
            <span className="font-medium text-white">{node.name || node.email}</span>
            {node.department && <span className="ml-2 text-white/50">• {node.department}</span>}
            <span className="ml-2 text-white/50">• {node.total_interactions} interactions</span>
          </div>
        )
      })()}
    </motion.div>
  )
}
