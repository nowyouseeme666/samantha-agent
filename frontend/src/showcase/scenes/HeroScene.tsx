import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Sphere, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

/** Particles floating in the background */
function ParticleField({ count = 200 }: { count?: number }) {
  const meshRef = useRef<THREE.Points>(null)
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 14
      p[i * 3 + 1] = (Math.random() - 0.5) * 8
      p[i * 3 + 2] = (Math.random() - 0.5) * 8
    }
    return p
  }, [count])

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.04
      meshRef.current.rotation.x += delta * 0.02
    }
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
        size={0.02}
        color="#c4956a"
        transparent
        opacity={0.6}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

/** Single orbiting ring with nodes */
function OrbitRing({
  radius,
  tilt,
  color,
  nodeCount,
  speed,
  nodeSize,
}: {
  radius: number
  tilt: [number, number, number]
  color: string
  nodeCount: number
  speed: number
  nodeSize?: number
}) {
  const groupRef = useRef<THREE.Group>(null)
  const nodes = useMemo(
    () =>
      Array.from({ length: nodeCount }, (_, i) => {
        const angle = (i / nodeCount) * Math.PI * 2
        return { angle, x: Math.cos(angle) * radius, z: Math.sin(angle) * radius }
      }),
    [radius, nodeCount],
  )

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * speed * 0.3
    }
  })

  const sz = nodeSize ?? 0.1

  return (
    <group ref={groupRef} rotation={tilt}>
      {/* Ring line */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[radius - 0.01, radius + 0.01, 128]} />
        <meshBasicMaterial color={color} transparent opacity={0.25} side={THREE.DoubleSide} />
      </mesh>
      {/* Nodes */}
      {nodes.map((n, i) => (
        <mesh key={i} position={[n.x, 0, n.z]}>
          <sphereGeometry args={[sz, 16, 16]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.6}
            roughness={0.3}
          />
        </mesh>
      ))}
    </group>
  )
}

/** Central Samantha core sphere with subtle distortion */
function CoreSphere() {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.15
    }
  })

  return (
    <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.4}>
      <Sphere ref={meshRef} args={[0.55, 64, 64]}>
        <MeshDistortMaterial
          color="#c4956a"
          emissive="#c4956a"
          emissiveIntensity={0.3}
          roughness={0.2}
          metalness={0.1}
          distort={0.15}
          speed={2}
        />
      </Sphere>
    </Float>
  )
}

/** Ambient lighting setup */
function Lighting() {
  return (
    <>
      <ambientLight intensity={0.3} color="#dcc4a8" />
      <pointLight position={[3, 2, 3]} intensity={1.2} color="#c4956a" />
      <pointLight position={[-3, -1, -2]} intensity={0.6} color="#8fa4c4" />
      <pointLight position={[0, 2, -2]} intensity={0.4} color="#dcc4a8" />
    </>
  )
}

export default function HeroScene() {
  return (
    <Canvas
      camera={{ position: [0, 0.3, 5.5], fov: 50 }}
      dpr={[1, 1.5]}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: true }}
    >
      <Lighting />
      <ParticleField count={250} />
      <CoreSphere />
      <OrbitRing
        radius={1.1}
        tilt={[Math.PI / 2.7, 0, 0]}
        color="#c4956a"
        nodeCount={6}
        speed={0.6}
        nodeSize={0.09}
      />
      <OrbitRing
        radius={1.5}
        tilt={[Math.PI / 1.8, Math.PI / 4, 0]}
        color="#8fa4c4"
        nodeCount={4}
        speed={-0.4}
        nodeSize={0.08}
      />
      <OrbitRing
        radius={1.9}
        tilt={[Math.PI / 2.2, -Math.PI / 5, 0]}
        color="#a8c97e"
        nodeCount={5}
        speed={0.5}
        nodeSize={0.07}
      />
    </Canvas>
  )
}
