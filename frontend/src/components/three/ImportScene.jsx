import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'

function Orb({ progress }) {
  const ref = useRef()
  useFrame(({ clock }) => {
    if (!ref.current) return
    ref.current.scale.setScalar(0.75 + progress * 0.6 + Math.sin(clock.elapsedTime * 2) * 0.04)
  })

  const color = useMemo(() => {
    const c = new THREE.Color('#3b82f6')
    c.lerp(new THREE.Color('#10b981'), progress)
    return c
  }, [progress])

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.8, 64, 64]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.4} roughness={0.25} metalness={0.1} />
    </mesh>
  )
}

function Ring({ progress }) {
  const ref = useRef()
  useFrame(() => {
    if (ref.current) {
      ref.current.rotation.z += 0.004
    }
  })

  return (
    <mesh ref={ref} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[1.5, 0.07, 24, 150, Math.max(progress, 0.03) * Math.PI * 2]} />
      <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.8} />
    </mesh>
  )
}

function EmailParticles() {
  const groupRef = useRef()
  const particles = useMemo(
    () =>
      Array.from({ length: 40 }, (_, i) => ({
        key: i,
        position: [(Math.random() - 0.5) * 6, (Math.random() - 0.5) * 4, (Math.random() - 0.5) * 4],
      })),
    [],
  )

  useFrame(() => {
    if (groupRef.current) groupRef.current.rotation.y += 0.002
  })

  return (
    <group ref={groupRef}>
      {particles.map((particle) => (
        <mesh key={particle.key} position={particle.position}>
          <boxGeometry args={[0.08, 0.08, 0.08]} />
          <meshStandardMaterial color="#60a5fa" emissive="#60a5fa" emissiveIntensity={0.3} />
        </mesh>
      ))}
    </group>
  )
}

export default function ImportScene({ percentage }) {
  const progress = Math.max(0, Math.min(1, percentage / 100))

  return (
    <div className="h-[340px] w-full overflow-hidden rounded-xl border border-white/20 bg-slate-950/40">
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[3, 4, 4]} intensity={3.2} color="#5eead4" />
        <pointLight position={[-3, -4, -3]} intensity={2.1} color="#60a5fa" />
        <EmailParticles />
        <Orb progress={progress} />
        <Ring progress={progress} />
        <OrbitControls enablePan={false} autoRotate autoRotateSpeed={0.7} maxDistance={8} minDistance={3} />
      </Canvas>
    </div>
  )
}
