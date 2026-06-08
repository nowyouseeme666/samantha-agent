import { useState, KeyboardEvent, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { if (!disabled) ref.current?.focus() }, [disabled])
  const send = () => { if (!text.trim() || disabled) return; onSend(text.trim()); setText('') }
  const handleKey = (e: KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', background: '#f3f0eb', borderRadius: 16, padding: '8px 12px', transition: 'box-shadow 0.2s' }} className='focus-within:ring-2 focus-within:ring-[#c4956a]'>
      <textarea ref={ref} value={text} onChange={e => setText(e.target.value)} onKeyDown={handleKey} placeholder="说点什么吧..."
        disabled={disabled} style={{ flex: 1, border: 'none', background: 'transparent', resize: 'none', outline: 'none', fontSize: 16, lineHeight: 1.5, color: '#2c2c2a', minHeight: 40, maxHeight: 120, fontFamily: 'inherit' }} rows={1} />
      <button onClick={send} disabled={disabled || !text.trim()} style={{ background: disabled || !text.trim() ? '#dcc4a8' : '#c4956a', border: 'none', color: 'white', borderRadius: 12, padding: '8px 16px', cursor: 'pointer', fontSize: 14, fontWeight: 500, transition: 'background 0.15s' }}>发送</button>
    </div>
  )
}
