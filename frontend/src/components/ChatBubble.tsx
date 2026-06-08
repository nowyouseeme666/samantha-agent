import type { Message } from '../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div style={{
        maxWidth: '70%', padding: '12px 16px', lineHeight: 1.6, fontSize: 16,
        background: isUser ? '#e8e4dc' : '#ffffff',
        borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
        boxShadow: isUser ? 'none' : '0 1px 3px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03)',
        color: '#2c2c2a', wordBreak: 'break-word'
      }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
      </div>
    </div>
  )
}
