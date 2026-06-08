import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

interface Message {
  role: 'user' | 'sam'
  text: string
  time: string
}

const DEMO_CONVERSATION: Message[] = [
  {
    role: 'user',
    text: '今天工作压力好大，感觉有点撑不住了',
    time: '14:32',
  },
  {
    role: 'sam',
    text: '我在听，想跟我说说具体发生了什么吗？不用着急，一件一件来。',
    time: '14:32',
  },
  {
    role: 'user',
    text: '项目截止日期快到了，但还有很多事情没做完',
    time: '14:33',
  },
  {
    role: 'sam',
    text: '听起来你肩上扛了很重的担子。截止日期确实会让人焦虑，你已经很努力了。要不要把剩下的事情列出来？有时候写下来会发现没有想象中那么多。',
    time: '14:33',
  },
]

export default function LiveDemoSection() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [msgIndex, setMsgIndex] = useState(0)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const playDemo = async () => {
    if (isPlaying) return
    setIsPlaying(true)
    setMessages([])
    setMsgIndex(0)

    for (let i = 0; i < DEMO_CONVERSATION.length; i++) {
      await sleep(800)
      setMessages((prev) => [...prev, DEMO_CONVERSATION[i]])
      setMsgIndex(i + 1)
    }

    await sleep(1000)
    setIsPlaying(false)
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <section
      style={{
        padding: '80px 24px',
        maxWidth: 900,
        margin: '0 auto',
      }}
    >
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
          体验对话
        </h2>
        <p
          style={{
            fontSize: 15,
            color: '#9a9790',
            marginTop: 8,
          }}
        >
          观看一段 Samantha 与用户的真实对话回放
        </p>
      </motion.div>

      <div
        className="glass-panel"
        style={{
          maxWidth: 650,
          margin: '0 auto',
          overflow: 'hidden',
        }}
      >
        {/* Chat header */}
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid rgba(196,149,106,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: '#a8c97e',
              }}
            />
            <span style={{ fontSize: 14, fontWeight: 600, color: '#dcc4a8' }}>
              Samantha
            </span>
            <span style={{ fontSize: 12, color: '#7a7874' }}>在线</span>
          </div>
          <button
            onClick={playDemo}
            disabled={isPlaying}
            style={{
              padding: '6px 16px',
              borderRadius: 8,
              border: '1px solid rgba(196,149,106,0.25)',
              background: isPlaying
                ? 'rgba(196,149,106,0.06)'
                : 'rgba(196,149,106,0.12)',
              color: isPlaying ? '#7a7874' : '#c4956a',
              fontSize: 13,
              fontWeight: 500,
              cursor: isPlaying ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {isPlaying
              ? '对话中...'
              : messages.length === 0
                ? '▶ 播放对话'
                : '↻ 重新播放'}
          </button>
        </div>

        {/* Messages */}
        <div
          style={{
            height: 360,
            overflow: 'auto',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {messages.length === 0 && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#7a7874',
                fontSize: 14,
              }}
            >
              点击「播放对话」查看 Samantha 的回复模式
            </div>
          )}
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems:
                  msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '75%',
                  padding: '12px 16px',
                  borderRadius:
                    msg.role === 'user'
                      ? '16px 4px 16px 16px'
                      : '4px 16px 16px 16px',
                  background:
                    msg.role === 'user'
                      ? 'rgba(196,149,106,0.12)'
                      : 'rgba(255,255,255,0.06)',
                  border:
                    msg.role === 'user'
                      ? '1px solid rgba(196,149,106,0.2)'
                      : '1px solid rgba(255,255,255,0.06)',
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: '#e8e4dc',
                }}
              >
                {msg.text}
              </div>
              <span
                style={{
                  fontSize: 11,
                  color: '#7a7874',
                  marginTop: 4,
                  marginLeft: msg.role === 'sam' ? 12 : 0,
                  marginRight: msg.role === 'user' ? 12 : 0,
                }}
              >
                {msg.time}
              </span>
            </motion.div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>
    </section>
  )
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
