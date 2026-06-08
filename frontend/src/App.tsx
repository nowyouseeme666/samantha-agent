import { useEffect, useState } from 'react'
import { useStore } from './store'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import EmotionPanel from './components/EmotionPanel'
import MemoryPanel from './components/MemoryPanel'

export default function App() {
  const loadConversations = useStore(s => s.loadConversations)
  const loadMemoryStats = useStore(s => s.loadMemoryStats)
  const loadEmotion = useStore(s => s.loadEmotion)
  const currentConvId = useStore(s => s.currentConvId)
  const loadConversation = useStore(s => s.loadConversation)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => { loadConversations(); loadMemoryStats(); loadEmotion() }, [])
  useEffect(() => { if (currentConvId) loadConversation(currentConvId) }, [currentConvId])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ height: 48, display: 'flex', alignItems: 'center', padding: '0 16px', borderBottom: '1px solid rgba(196,149,106,0.15)', justifyContent: 'space-between' }}>
        <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#c4956a', fontSize: 20 }}>&#9776;</button>
        <span style={{ fontWeight: 600, fontSize: 16, color: '#2c2c2a' }}>Samantha <span style={{ fontWeight: 400, color: '#7a7874', fontSize: 14 }}>- Emotional Companion</span></span>
        <div style={{ width: 32 }} />
      </header>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {sidebarOpen && <Sidebar onClose={() => setSidebarOpen(false)} />}
        <ChatArea />
        <div style={{ width: 240, borderLeft: '1px solid rgba(196,149,106,0.12)', padding: 16, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'auto' }} className='hidden lg:flex'>
          <EmotionPanel />
          <MemoryPanel />
        </div>
      </div>
    </div>
  )
}
