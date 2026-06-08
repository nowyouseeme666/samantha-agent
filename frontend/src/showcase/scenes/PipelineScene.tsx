import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float } from '@react-three/drei'
import * as THREE from 'three'
import { PIPELINE_STEPS, type PipelineStep } from '../data/content'

/** Particle stream between two points */
function ParticleStream({
  start,
  end,
  color,
  active,
}: {
  start: [number, number, number]
  end: [number, number, number]
  color: string
  active: boolean
}) {
  const meshRef = useRef<THREE.Points>(null)
  const count = 30
  const positions = useMemo(() => new Float32Array(count * 3), [count])
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    return g
  }, [positions])

  useFrame(() => {
    if (!meshRef.current || !active) return
    const pos = (meshRef.current.geometry.attributes.position as THREE.BufferAttribute).array as Float32Array
    for (let i = 0; i < count; i++) {
      const t = ((Date.now() * 0.001 + i * 0.1) % 1.5) / 1.5
      pos[i * 3] = start[0] + (end[0] - start[0]) * t
      pos[i * 3 + 1] = start[1] + (end[1] - start[1]) * t
      pos[i * 3 + 2] = start[2] + (end[2] - start[2]) * t
    }
    ;(meshRef.current.geometry.attributes.position as THREE.BufferAttribute).needsUpdate = true
  })

  const mat = useMemo(
    () =>
      new THREE.PointsMaterial({
        size: 0.04,
        color,
        transparent: true,
        opacity: active ? 0.8 : 0,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    [color, active],
  )

  return <points ref={meshRef} geometry={geometry} material={mat} />
}

function PipelineNode({
  step,
  position,
  active,
}: {
  step: PipelineStep
  position: [number, number, number]
  active: boolean
}) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.3
      meshRef.current.rotation.x += delta * 0.15
      const s = active ? 1.15 : 0.85
      meshRef.current.scale.lerp(
        new THREE.Vector3(s, s, s),
        0.1,
      )
    }
  })

  const geometry = useMemo(() => {
    switch (step.shape) {
      case 'box':
        return <boxGeometry args={[0.35, 0.35, 0.35]} />
      case 'cylinder':
        return <cylinderGeometry args={[0.18, 0.18, 0.4, 32]} />
      case 'sphere':
        return <sphereGeometry args={[0.2, 32, 32]} />
      case 'torus':
        return <torusGeometry args={[0.15, 0.06, 16, 32]} />
      case 'octahedron':
        return <octahedronGeometry args={[0.2, 0]} />
      case 'cone':
        return <coneGeometry args={[0.18, 0.4, 32]} />
    }
  }, [step.shape])

  return (
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.15}>
      <group position={position}>
        <mesh ref={meshRef}>
          {geometry}
          <meshStandardMaterial
            color={step.color}
            emissive={step.color}
            emissiveIntensity={active ? 0.7 : 0.15}
            roughness={0.3}
            metalness={0.1}
          />
        </mesh>
        {/* Glow ring */}
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.28, 0.32, 64]} />
          <meshBasicMaterial
            color={step.color}
            transparent
            opacity={active ? 0.4 : 0.05}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
    </Float>
  )
}

function Lighting() {
  return (
    <>
      <ambientLight intensity={0.3} color="#dcc4a8" />
      <pointLight position={[0, 3, 4]} intensity={1} color="#c4956a" />
      <pointLight position={[0, -1, 2]} intensity={0.4} color="#8fa4c4" />
    </>
  )
}

export default function PipelineScene({
  activeIndex,
}: {
  activeIndex: number
}) {
  const spacing = 1.35
  const startX = -(PIPELINE_STEPS.length - 1) * spacing * 0.5
  const safeIndex = Math.min(activeIndex, PIPELINE_STEPS.length - 1)

  return (
    <Canvas
      camera={{ position: [0, 0.4, 5.5], fov: 50 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <Lighting />
      {PIPELINE_STEPS.map((step, i) => {
        const x = startX + i * spacing
        const isActive = i <= safeIndex
        return (
          <group key={step.id}>
            <PipelineNode
              step={step}
              position={[x, 0, 0]}
              active={isActive}
            />
            {i < PIPELINE_STEPS.length - 1 && (
              <ParticleStream
                start={[x + 0.25, 0, 0]}
                end={[x + spacing - 0.25, 0, 0]}
                color={step.color}
                active={isActive && i < safeIndex}
              />
            )}
          </group>
        )
      })}
    </Canvas>
  )
}
