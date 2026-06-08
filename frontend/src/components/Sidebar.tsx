import { useStore } from '../store'
import ConversationList from './ConversationList'
import StatsCard from './StatsCard'

export default function Sidebar({ onClose }: { onClose: () => void }) {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ width: 240, background: '#faf9f7', height: '100%', display: 'flex', flexDirection: 'column', padding: 16, gap: 16, overflow: 'auto', boxShadow: '2px 0 12px rgba(0,0,0,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600, fontSize: 14, color: '#2c2c2a' }}>对话列表</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#7a7874', fontSize: 18 }}>&times;</button>
        </div>
        <ConversationList />
        <StatsCard />
      </div>
    </div>
  )
}
