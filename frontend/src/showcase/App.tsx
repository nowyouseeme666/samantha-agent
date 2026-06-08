import { useRef, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import HeroSection from './sections/HeroSection'
import PipelineSection from './sections/PipelineSection'
import PillarsSection from './sections/PillarsSection'
import ToolSection from './sections/ToolSection'
import LiveDemoSection from './sections/LiveDemoSection'

export default function ShowcaseApp() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [pipelineActive, setPipelineActive] = useState(-1)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  return (
    <div
      ref={containerRef}
      style={{ background: '#1a1917', color: '#e8e4dc' }}
    >
      {/* Fixed nav */}
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 24px',
          background: 'rgba(26, 25, 23, 0.85)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(196, 149, 106, 0.12)',
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 15, color: '#c4956a' }}>
          Samantha Agent
        </span>
        <span style={{ fontSize: 13, color: '#9a9790' }}>
          架构展示
        </span>
      </nav>

      <HeroSection />
      <PipelineSection
        scrollProgress={scrollYProgress}
        activeIndex={pipelineActive}
        onStepEnter={setPipelineActive}
      />
      <PillarsSection />
      <ToolSection />
      <LiveDemoSection />

      {/* Footer */}
      <footer
        style={{
          textAlign: 'center',
          padding: '48px 24px',
          color: '#7a7874',
          fontSize: 13,
          borderTop: '1px solid rgba(196, 149, 106, 0.08)',
        }}
      >
        <p>Samantha Agent · Python / LangChain / LangGraph / ChromaDB / DeepSeek</p>
        <p style={{ marginTop: 4, fontSize: 12, color: '#5a5854' }}>
          Built with Three.js · React Three Fiber · Framer Motion
        </p>
      </footer>
    </div>
  )
}
