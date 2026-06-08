import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Text } from '@react-three/drei'
import * as THREE from 'three'
import type { ToolDef } from '../data/content'

/** Animated data flow for a single tool execution */
function ToolDataFlow({
  tool,
  phase,
}: {
  tool: ToolDef
  phase: 'idle' | 'input' | 'process' | 'output'
}) {
  const groupRef = useRef<THREE.Group>(null)
  const processorRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.15
    }
    if (processorRef.current && phase === 'process') {
      processorRef.current.rotation.z += delta * 3
      const s = 1 + Math.sin(Date.now() * 0.01) * 0.1
      processorRef.current.scale.setScalar(s)
    }
    if (processorRef.current && phase !== 'process') {
      processorRef.current.rotation.z += delta * 0.3
      processorRef.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1)
    }
  })

  const inputOpacity = phase === 'input' || phase === 'process' ? 1 : 0.3
  const outputOpacity = phase === 'output' ? 1 : 0.3
  const procIntensity = phase === 'process' ? 1 : 0.3

  return (
    <group ref={groupRef}>
      {/* Input node */}
      <Float speed={2} rotationIntensity={0.2} floatIntensity={0.15}>
        <mesh position={[-0.9, 0, 0]}>
          <boxGeometry args={[0.3, 0.2, 0.2]} />
          <meshStandardMaterial
            color={tool.color}
            emissive={tool.color}
            emissiveIntensity={inputOpacity * 0.5}
            roughness={0.4}
            transparent
            opacity={inputOpacity}
          />
        </mesh>
      </Float>

      {/* Arrow / stream: input → processor */}
      <mesh position={[-0.55, 0, 0]}>
        <boxGeometry args={[0.3, 0.03, 0.03]} />
        <meshBasicMaterial
          color={tool.color}
          transparent
          opacity={inputOpacity * 0.6}
        />
      </mesh>

      {/* Processor — rotating gear-like */}
      <mesh ref={processorRef} position={[0, 0, 0]}>
        <torusGeometry args={[0.18, 0.06, 16, 32]} />
        <meshStandardMaterial
          color={tool.color}
          emissive={tool.color}
          emissiveIntensity={procIntensity}
          roughness={0.2}
          metalness={0.3}
        />
      </mesh>

      {/* Arrow / stream: processor → output */}
      <mesh position={[0.55, 0, 0]}>
        <boxGeometry args={[0.3, 0.03, 0.03]} />
        <meshBasicMaterial
          color={tool.color}
          transparent
          opacity={outputOpacity * 0.6}
        />
      </mesh>

      {/* Output node */}
      <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.1}>
        <mesh position={[0.9, 0, 0]}>
          <sphereGeometry args={[0.15, 32, 32]} />
          <meshStandardMaterial
            color={tool.color}
            emissive={tool.color}
            emissiveIntensity={outputOpacity * 0.6}
            roughness={0.3}
            transparent
            opacity={outputOpacity}
          />
        </mesh>
      </Float>

      {/* Data particles flowing through */}
      <DataParticles
        color={tool.color}
        visible={phase === 'process'}
      />
    </group>
  )
}

function DataParticles({
  color,
  visible,
}: {
  color: string
  visible: boolean
}) {
  const meshRef = useRef<THREE.Points>(null)
  const count = 20
  const positions = useMemo(() => new Float32Array(count * 3), [count])

  useFrame(() => {
    if (!meshRef.current || !visible) return
    const pos = meshRef.current.geometry.attributes.position
      .array as Float32Array
    for (let i = 0; i < count; i++) {
      const t = ((Date.now() * 0.001 + i * 0.15) % 1.8) / 1.8
      pos[i * 3] = -0.9 + t * 1.8
      pos[i * 3 + 1] = Math.sin(t * Math.PI * 3) * 0.15
      pos[i * 3 + 2] = Math.cos(t * Math.PI * 3) * 0.1
    }
    meshRef.current.geometry.attributes.position.needsUpdate = true
  })

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.025}
        color={color}
        transparent
        opacity={visible ? 0.9 : 0}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

function Lighting() {
  return (
    <>
      <ambientLight intensity={0.4} color="#dcc4a8" />
      <pointLight position={[2, 2, 3]} intensity={1} color="#c4956a" />
      <pointLight position={[-2, -1, 2]} intensity={0.4} color="#8fa4c4" />
    </>
  )
}

export default function ToolScene({
  tool,
  phase,
}: {
  tool: ToolDef
  phase: 'idle' | 'input' | 'process' | 'output'
}) {
  return (
    <Canvas
      camera={{ position: [0, 0.15, 3.2], fov: 50 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <Lighting />
      <ToolDataFlow tool={tool} phase={phase} />
    </Canvas>
  )
}
