import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ToolScene from '../scenes/ToolScene'
import { TOOLS, type ToolDef } from '../data/content'

type Phase = 'idle' | 'input' | 'process' | 'output'

export default function ToolSection() {
  const [selectedTool, setSelectedTool] = useState<ToolDef>(TOOLS[0])
  const [phase, setPhase] = useState<Phase>('idle')
  const [isAnimating, setIsAnimating] = useState(false)

  const runDemo = async () => {
    if (isAnimating) return
    setIsAnimating(true)
    setPhase('idle')
    await sleep(300)
    setPhase('input')
    await sleep(1200)
    setPhase('process')
    await sleep(1800)
    setPhase('output')
    await sleep(1500)
    setIsAnimating(false)
  }

  return (
    <section
      style={{
        padding: '80px 24px',
        maxWidth: 1200,
        margin: '0 auto',
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: 'center', marginBottom: 56 }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 700,
            color: '#e8e4dc',
            margin: 0,
          }}
        >
          工具调用可视化
        </h2>
        <p
          style={{
            fontSize: 15,
            color: '#9a9790',
            marginTop: 8,
          }}
        >
          选择一个工具，观察输入 → 处理 → 输出的完整数据流
        </p>
      </motion.div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
        }}
      >
        {/* Tool selector */}
        <div
          style={{
            display: 'flex',
            gap: 10,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {TOOLS.map((tool) => (
            <button
              key={tool.name}
              onClick={() => {
                setSelectedTool(tool)
                setPhase('idle')
              }}
              disabled={isAnimating}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '10px 18px',
                borderRadius: 12,
                border:
                  selectedTool.name === tool.name
                    ? `1px solid ${tool.color}60`
                    : '1px solid rgba(255,255,255,0.08)',
                background:
                  selectedTool.name === tool.name
                    ? `${tool.color}14`
                    : 'rgba(255,255,255,0.03)',
                color:
                  selectedTool.name === tool.name
                    ? tool.color
                    : '#9a9790',
                fontSize: 14,
                fontWeight:
                  selectedTool.name === tool.name ? 600 : 400,
                cursor: isAnimating ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                opacity: isAnimating ? 0.6 : 1,
              }}
            >
              <span>{tool.icon}</span>
              <span>{tool.label}</span>
            </button>
          ))}
        </div>

        {/* 3D visualization + data panel */}
        <div
          className="glass-panel tool-showcase-grid"
          style={{
            overflow: 'hidden',
            minHeight: 420,
          }}
        >
          {/* 3D Scene */}
          <div
            style={{
              position: 'relative',
              minHeight: 400,
            }}
          >
            <ToolScene tool={selectedTool} phase={phase} />

            {/* Phase indicator */}
            <AnimatePresence mode="wait">
              <motion.div
                key={phase}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
                style={{
                  position: 'absolute',
                  top: 16,
                  left: 16,
                  padding: '6px 14px',
                  borderRadius: 8,
                  background: phase === 'idle' ? 'rgba(255,255,255,0.04)' :
                    phase === 'input' ? `${selectedTool.color}18` :
                    phase === 'process' ? `${selectedTool.color}28` :
                    `${selectedTool.color}18`,
                  border: `1px solid ${phase === 'idle' ? 'rgba(255,255,255,0.08)' : selectedTool.color}40`,
                  fontSize: 12,
                  fontWeight: 600,
                  color: phase === 'idle' ? '#9a9790' : selectedTool.color,
                }}
              >
                {phase === 'idle'
                  ? '就绪'
                  : phase === 'input'
                    ? '接收输入'
                    : phase === 'process'
                      ? '处理中...'
                      : '输出结果'}
              </motion.div>
            </AnimatePresence>

            {/* Demo button */}
            <button
              onClick={runDemo}
              disabled={isAnimating}
              style={{
                position: 'absolute',
                bottom: 16,
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '10px 28px',
                borderRadius: 12,
                border: '1px solid rgba(196,149,106,0.3)',
                background: isAnimating
                  ? 'rgba(196,149,106,0.08)'
                  : 'rgba(196,149,106,0.14)',
                color: isAnimating ? '#9a9790' : '#c4956a',
                fontSize: 14,
                fontWeight: 600,
                cursor: isAnimating ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              {isAnimating ? '演示中...' : '▶ 运行动态演示'}
            </button>
          </div>

          {/* Data panel */}
          <div
            style={{
              padding: 24,
              borderLeft: '1px solid rgba(196,149,106,0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
              overflow: 'auto',
            }}
          >
            <div>
              <h4
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: '#dcc4a8',
                  marginBottom: 4,
                }}
              >
                {selectedTool.icon} {selectedTool.label}
              </h4>
              <p
                style={{
                  fontSize: 13,
                  color: '#9a9790',
                  lineHeight: 1.6,
                }}
              >
                {selectedTool.description}
              </p>
            </div>

            {/* Inputs */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#7a7874',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: 8,
                }}
              >
                输入参数
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                {selectedTool.inputs.map((inp, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0.4 }}
                    animate={{
                      opacity: phase === 'input' || phase === 'process' || phase === 'output' ? 1 : 0.4,
                    }}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 10,
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.06)',
                      fontSize: 13,
                    }}
                  >
                    <div style={{ color: '#7a7874', fontSize: 11, marginBottom: 2 }}>
                      {inp.label}
                    </div>
                    <div
                      style={{
                        color: '#dcc4a8',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 12,
                      }}
                    >
                      {inp.example}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div style={{ textAlign: 'center', color: '#c4956a', fontSize: 20 }}>
              ↓
            </div>

            {/* Outputs */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#7a7874',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: 8,
                }}
              >
                输出结果
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                {selectedTool.outputs.map((out, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0.4 }}
                    animate={{
                      opacity: phase === 'output' ? 1 : 0.4,
                    }}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 10,
                      background:
                        phase === 'output'
                          ? `${selectedTool.color}10`
                          : 'rgba(255,255,255,0.03)',
                      border:
                        phase === 'output'
                          ? `1px solid ${selectedTool.color}30`
                          : '1px solid rgba(255,255,255,0.06)',
                      fontSize: 13,
                    }}
                  >
                    <div style={{ color: '#7a7874', fontSize: 11, marginBottom: 2 }}>
                      {out.label}
                    </div>
                    <div
                      style={{
                        color: phase === 'output' ? selectedTool.color : '#dcc4a8',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 12,
                      }}
                    >
                      {out.example}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
