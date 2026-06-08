import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float } from '@react-three/drei'
import * as THREE from 'three'
import { MEMORY_LAYERS } from '../data/content'

/** Three stacked rotating discs — memory layers */
function MemoryLayersScene() {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * 0.2
  })

  return (
    <group ref={groupRef}>
      {MEMORY_LAYERS.map((layer, i) => (
        <Float
          key={layer.name}
          speed={1 + i * 0.3}
          rotationIntensity={0.15}
          floatIntensity={0.2}
        >
          <mesh position={[0, i * 0.15 - 0.15, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <torusGeometry args={[layer.radius, 0.04, 16, 80]} />
            <meshStandardMaterial
              color={layer.color}
              emissive={layer.color}
              emissiveIntensity={0.5}
              roughness={0.3}
              transparent
              opacity={0.8}
            />
          </mesh>
        </Float>
      ))}
      {/* Core sphere */}
      <mesh>
        <sphereGeometry args={[0.2, 32, 32]} />
        <meshStandardMaterial
          color="#c4956a"
          emissive="#c4956a"
          emissiveIntensity={0.6}
          roughness={0.2}
        />
      </mesh>
    </group>
  )
}

/** Valence/Arousal point on 2D plane */
function EmotionScene() {
  const dotRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    const t = Date.now() * 0.001
    // Simulate emotion wandering
    const vx = Math.sin(t * 0.7) * 0.6
    const vy = Math.cos(t * 0.5) * 0.5
    if (dotRef.current) {
      dotRef.current.position.x = vx
      dotRef.current.position.y = vy
    }
    if (glowRef.current) {
      glowRef.current.position.copy(dotRef.current!.position)
      const s = 1 + Math.sin(t * 2) * 0.15
      glowRef.current.scale.setScalar(s)
    }
  })

  return (
    <group>
      {/* Background plane */}
      <mesh position={[0, 0, -0.05]}>
        <planeGeometry args={[2.4, 2]} />
        <meshBasicMaterial color="#1a1917" transparent opacity={0.3} />
      </mesh>
      {/* Cross axes */}
      <mesh position={[0, 0, -0.03]}>
        <planeGeometry args={[2, 0.015]} />
        <meshBasicMaterial color="#7a7874" transparent opacity={0.3} />
      </mesh>
      <mesh position={[0, 0, -0.03]}>
        <planeGeometry args={[0.015, 1.6]} />
        <meshBasicMaterial color="#7a7874" transparent opacity={0.3} />
      </mesh>
      {/* Glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.1, 32, 32]} />
        <meshBasicMaterial color="#a8c97e" transparent opacity={0.2} />
      </mesh>
      {/* Dot */}
      <mesh ref={dotRef}>
        <sphereGeometry args={[0.06, 32, 32]} />
        <meshStandardMaterial
          color="#a8c97e"
          emissive="#a8c97e"
          emissiveIntensity={1}
          roughness={0.2}
        />
      </mesh>
    </group>
  )
}

/** Central hub with orbiting tool nodes */
function ToolsScene() {
  const groupRef = useRef<THREE.Group>(null)
  const TOOL_COLORS = ['#8fa4c4', '#a8c97e', '#d4a574', '#c4956a', '#dcc4a8']

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * 0.4
  })

  return (
    <group ref={groupRef}>
      {/* Hub */}
      <mesh>
        <icosahedronGeometry args={[0.2, 0]} />
        <meshStandardMaterial
          color="#c4956a"
          emissive="#c4956a"
          emissiveIntensity={0.5}
          roughness={0.3}
        />
      </mesh>
      {/* Connections to tools */}
      {Array.from({ length: 5 }, (_, i) => {
        const angle = (i / 5) * Math.PI * 2
        const r = 0.7
        const x = Math.cos(angle) * r
        const z = Math.sin(angle) * r
        return (
          <group key={i}>
            <mesh position={[x / 2, 0, z / 2]} rotation={[0, 0, -angle]}>
              <cylinderGeometry args={[0.012, 0.012, r, 8]} />
              <meshBasicMaterial
                color={TOOL_COLORS[i]}
                transparent
                opacity={0.4}
              />
            </mesh>
            <Float speed={2} rotationIntensity={0.3} floatIntensity={0.2}>
              <mesh position={[x, 0, z]}>
                <sphereGeometry args={[0.07, 16, 16]} />
                <meshStandardMaterial
                  color={TOOL_COLORS[i]}
                  emissive={TOOL_COLORS[i]}
                  emissiveIntensity={0.5}
                  roughness={0.3}
                />
              </mesh>
            </Float>
          </group>
        )
      })}
    </group>
  )
}

function MiniLighting() {
  return (
    <>
      <ambientLight intensity={0.4} color="#dcc4a8" />
      <pointLight position={[2, 2, 3]} intensity={0.8} color="#c4956a" />
    </>
  )
}

export function MemoryLayersCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0.5, 4.5], fov: 45 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <MiniLighting />
      <MemoryLayersScene />
    </Canvas>
  )
}

export function EmotionCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0, 4], fov: 45 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <MiniLighting />
      <EmotionScene />
    </Canvas>
  )
}

export function ToolsCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0.5, 3.5], fov: 45 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <MiniLighting />
      <ToolsScene />
    </Canvas>
  )
}
