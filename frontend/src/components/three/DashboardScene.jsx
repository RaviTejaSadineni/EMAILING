import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'

function FloatingGrid() {
  const ref = useRef()
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.x = Math.sin(clock.elapsedTime * 0.1) * 0.05
      ref.current.rotation.y = clock.elapsedTime * 0.03
    }
  })

  const points = useMemo(() => {
    const pts = []
    for (let i = -5; i <= 5; i++) {
      for (let j = -5; j <= 5; j++) {
        pts.push(new THREE.Vector3(i * 0.8, j * 0.8, 0))
      }
    }
    return pts
  }, [])

  return (
    <group ref={ref} position={[0, 0, -3]}>
      {points.map((pt, i) => (
        <mesh key={i} position={pt}>
          <sphereGeometry args={[0.02, 8, 8]} />
          <meshBasicMaterial color="#667eea" transparent opacity={0.3} />
        </mesh>
      ))}
    </group>
  )
}

function GlowOrb({ position, color, size = 0.3 }) {
  const ref = useRef()
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.position.y = position[1] + Math.sin(clock.elapsedTime * 0.5 + position[0]) * 0.3
      ref.current.scale.setScalar(size + Math.sin(clock.elapsedTime + position[0]) * 0.05)
    }
  })

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[1, 32, 32]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} transparent opacity={0.15} />
    </mesh>
  )
}

export default function DashboardScene() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 opacity-40">
      <Canvas camera={{ position: [0, 0, 6], fov: 50 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} intensity={1} color="#667eea" />
        <pointLight position={[-5, -3, 3]} intensity={0.5} color="#764ba2" />
        <FloatingGrid />
        <GlowOrb position={[-3, 2, -1]} color="#667eea" size={0.5} />
        <GlowOrb position={[3, -1, -2]} color="#764ba2" size={0.4} />
        <GlowOrb position={[0, 3, -1]} color="#10b981" size={0.3} />
      </Canvas>
    </div>
  )
}
