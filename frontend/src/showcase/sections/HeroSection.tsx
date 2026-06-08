import { motion } from 'framer-motion'
import HeroScene from '../scenes/HeroScene'

export default function HeroSection() {
  return (
    <section
      style={{
        position: 'relative',
        height: '100vh',
        minHeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* 3D Scene Background */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <HeroScene />
      </div>

      {/* Gradient fades at edges */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at center, transparent 40%, rgba(26,25,23,0.7) 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '30%',
          background:
            'linear-gradient(to top, rgba(26,25,23,1), transparent)',
          pointerEvents: 'none',
        }}
      />

      {/* Text overlay */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: 'easeOut' }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          padding: '0 24px',
          maxWidth: 720,
        }}
      >
        <p
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: '#c4956a',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            marginBottom: 16,
          }}
        >
          AI Agent Architecture
        </p>
        <h1
          style={{
            fontSize: 'clamp(2rem, 5vw, 3.5rem)',
            fontWeight: 700,
            lineHeight: 1.2,
            color: '#e8e4dc',
            margin: 0,
            textWrap: 'balance' as const,
          }}
        >
          Samantha
          <span style={{ color: '#c4956a', fontWeight: 500 }}> Agent</span>
        </h1>
        <p
          style={{
            fontSize: 'clamp(1rem, 2vw, 1.25rem)',
            color: '#9a9790',
            marginTop: 16,
            lineHeight: 1.6,
            textWrap: 'balance' as const,
          }}
        >
          三层记忆 · 情绪感知 · 智能工具调用
          <br />
          一个能理解你的情感陪伴 AI 助手
        </p>
        <div style={{ marginTop: 32 }}>
          <span
            style={{
              display: 'inline-block',
              color: '#9a9790',
              fontSize: 13,
              borderBottom: '1px solid rgba(196,149,106,0.3)',
              paddingBottom: 4,
            }}
          >
            向下滚动探索架构
          </span>
        </div>
      </motion.div>
    </section>
  )
}
