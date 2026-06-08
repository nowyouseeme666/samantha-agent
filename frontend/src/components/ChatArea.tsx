import { useEffect, useRef } from 'react'
import { useStore } from '../store'
import ChatBubble from './ChatBubble'
import ChatInput from './ChatInput'

export default function ChatArea() {
  const messages = useStore(s => s.messages)
  const isLoading = useStore(s => s.isLoading)
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  const send = async (content: string) => { const g = useStore.getState().sendMessage(content); for await (const _ of g) {} }
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: '65ch', margin: '0 auto', width: '100%', padding: '0 16px' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: '24px 0', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#7a7874', fontSize: 15 }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>&#127769;</div>
            <div>晚上好，我是 Samantha，今天过得怎么样？</div>
          </div>
        )}
        {messages.map(m => <ChatBubble key={m.id} message={m} />)}
        <div ref={bottomRef} />
      </div>
      <div style={{ padding: '16px 0' }}><ChatInput onSend={send} disabled={isLoading} /></div>
    </div>
  )
}
