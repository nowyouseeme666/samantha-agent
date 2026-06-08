import { useEffect, useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import PipelineScene from '../scenes/PipelineScene'
import { PIPELINE_STEPS } from '../data/content'

export default function PipelineSection({
  scrollProgress,
  activeIndex,
  onStepEnter,
}: {
  scrollProgress: any
  activeIndex: number
  onStepEnter: (i: number) => void
}) {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { amount: 0.3 })
  const [localActive, setLocalActive] = useState(-1)

  // Animate nodes sequentially on scroll into view
  useEffect(() => {
    if (!isInView) {
      setLocalActive(-1)
      return
    }
    let cancelled = false
    const run = async () => {
      for (let i = 0; i < PIPELINE_STEPS.length; i++) {
        if (cancelled) return
        setLocalActive(i)
        onStepEnter(i)
        await new Promise((r) => setTimeout(r, 600))
      }
    }
    run()
    return () => { cancelled = true }
  }, [isInView])

  return (
    <section
      ref={sectionRef}
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        padding: '80px 24px',
      }}
    >
      {/* Section header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: 'center', marginBottom: 48 }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 700,
            color: '#e8e4dc',
            margin: 0,
          }}
        >
          处理管线
        </h2>
        <p
          style={{
            fontSize: 15,
            color: '#9a9790',
            marginTop: 8,
          }}
        >
          从用户消息到温暖回复的完整流程
        </p>
      </motion.div>

      {/* 3D Pipeline Scene */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          minHeight: 400,
          borderRadius: 20,
          overflow: 'hidden',
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(196,149,106,0.1)',
        }}
      >
        <PipelineScene activeIndex={localActive} />

        {/* Step labels overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: 24,
            left: 0,
            right: 0,
            display: 'flex',
            justifyContent: 'center',
            gap: 8,
            flexWrap: 'wrap',
            padding: '0 16px',
          }}
        >
          {PIPELINE_STEPS.map((step, i) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0.3 }}
              animate={{
                opacity: i <= localActive ? 1 : 0.3,
                scale: i <= localActive ? 1 : 0.95,
              }}
              transition={{ duration: 0.4 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 10,
                background:
                  i <= localActive
                    ? `${step.color}18`
                    : 'rgba(255,255,255,0.03)',
                border:
                  i <= localActive
                    ? `1px solid ${step.color}40`
                    : '1px solid rgba(255,255,255,0.06)',
                fontSize: 13,
                color: i <= localActive ? step.color : '#7a7874',
              }}
            >
              {/* Shape indicator */}
              <span style={{ fontSize: 10 }}>
                {step.shape === 'box'
                  ? '◆'
                  : step.shape === 'sphere'
                    ? '●'
                    : step.shape === 'cylinder'
                      ? '⬡'
                      : step.shape === 'torus'
                        ? '◎'
                        : step.shape === 'octahedron'
                          ? '◆'
                          : '▲'}
              </span>
              <span style={{ fontWeight: i <= localActive ? 600 : 400 }}>
                {step.label}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
