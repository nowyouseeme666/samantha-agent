import { motion } from 'framer-motion'
import {
  MemoryLayersCanvas,
  EmotionCanvas,
  ToolsCanvas,
} from '../scenes/PillarsScene'
import { MEMORY_LAYERS } from '../data/content'

const pillars = [
  {
    title: '三层记忆',
    subtitle: 'Three-Layer Memory',
    details: MEMORY_LAYERS,
    scene: <MemoryLayersCanvas />,
  },
  {
    title: '情绪检测',
    subtitle: 'Emotion Detection',
    details: [
      {
        name: '规则匹配',
        sub: 'Rule-based',
        desc: '关键词快速匹配，高置信度优先。',
        color: '#a8c97e',
      },
      {
        name: 'LLM 识别',
        sub: 'LLM Fallback',
        desc: '规则未命中时 LLM 推理情绪。',
        color: '#c4956a',
      },
      {
        name: 'Valence/Arousal',
        sub: 'Dimensional Model',
        desc: '二维情绪空间：效价 + 唤醒度。',
        color: '#8fa4c4',
      },
    ],
    scene: <EmotionCanvas />,
  },
  {
    title: '工具调用',
    subtitle: 'Tool Calling',
    details: [
      {
        name: '5 个工具',
        sub: 'Built-in Tools',
        desc: '记忆搜索、情绪日记、提醒、音乐推荐、天气。',
        color: '#d4a574',
      },
      {
        name: 'ToolExecutor',
        sub: 'Execution Engine',
        desc: '统一执行器，批处理并发，未知工具优雅降级。',
        color: '#c4956a',
      },
      {
        name: '上下文注入',
        sub: 'Context Injection',
        desc: '工具返回结果自动注入 LLM 上下文。',
        color: '#dcc4a8',
      },
    ],
    scene: <ToolsCanvas />,
  },
]

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6, ease: 'easeOut' },
  }),
}

export default function PillarsSection() {
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
          三大核心能力
        </h2>
        <p
          style={{
            fontSize: 15,
            color: '#9a9790',
            marginTop: 8,
          }}
        >
          每个模块独立设计，统一编排
        </p>
      </motion.div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 24,
        }}
      >
        {pillars.map((pillar, i) => (
          <motion.div
            key={pillar.title}
            custom={i}
            variants={cardVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            className="glass-panel"
            style={{
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* 3D Scene */}
            <div
              style={{
                position: 'relative',
                height: 240,
                overflow: 'hidden',
              }}
            >
              {pillar.scene}
            </div>

            {/* Content */}
            <div
              style={{
                padding: '20px 24px 24px',
                borderTop: '1px solid rgba(196,149,106,0.1)',
              }}
            >
              <h3
                style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: '#e8e4dc',
                  margin: 0,
                }}
              >
                {pillar.title}
              </h3>
              <p
                style={{
                  fontSize: 13,
                  color: '#9a9790',
                  margin: '4px 0 16px',
                }}
              >
                {pillar.subtitle}
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {pillar.details.map((d: any, j: number) => (
                  <div
                    key={d.name}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 10,
                    }}
                  >
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: d.color,
                        marginTop: 4,
                        flexShrink: 0,
                      }}
                    />
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: '#dcc4a8' }}>
                        {d.name}
                      </div>
                      {d.sub && (
                        <div style={{ fontSize: 11, color: '#7a7874', marginBottom: 2 }}>
                          {d.sub}
                        </div>
                      )}
                      <div style={{ fontSize: 13, color: '#9a9790', lineHeight: 1.5 }}>
                        {d.desc}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
